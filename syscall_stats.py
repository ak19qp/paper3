# load proper Trace Compass modules
loadModule('/TraceCompass/Analysis');
loadModule('/TraceCompass/Trace');
loadModule('/TraceCompass/View');
loadModule('/TraceCompass/DataProvider');

from py4j.java_gateway import JavaClass
from datetime import datetime
import os

try: 
    os.mkdir("csv")
except OSError as error: 
    print(error)  




print("Start")

# Get the active trace
trace = getActiveTrace()

block_requests = []
syscalls = []

# Create an analysis for this script
analysis = createScriptedAnalysis(trace, "activetid_python.js")

if analysis is None:
    print("Trace is null")
    exit()

# Get the analysis's state system so we can fill it, true indicates to re-use an existing state system, false would create a new state system even if one already exists
ss = analysis.getStateSystem(False)

# The state system methods require a vararg array. This puts the string in a vararg array to call those methods
def strToVarargs(str):
    object_class = java.lang.String
    object_array = gateway.new_array(object_class, 1)
    object_array[0] = str
    return object_array


def time_str_to_int(time):
    time = time.replace(" ", "")
    time_list = time.split(":")
    time_builder = (float(time_list[0]) * 3600) + (float(time_list[1]) * 60) + float(time_list[2])

    return time_builder

# The analysis itself is in this function
def runAnalysis(count=-1):
    # Get the event iterator for the trace
    iter = analysis.getEventIterator()
   
    # Parse all events
    event = None

  
    
    syscall_entry_list = []
    syscall_entry_Timestamp_list  = []

    unique_functions = []
    

    if count != -1:
            count = count + 1

    while iter.hasNext():

        if count != -1 and count > 0:
            count = count -1
            print(count)
        
        if count == 0:
            break

        # The python java gateway keeps a reference to the Java objects it sends to python. To avoid OutOfMemoryException, they need to be explicitly detached from the gateway when not needed anymore
        if not(event is None):
            gateway.detach(event)
        
        event = iter.next();

        print("Processing: "+str(getEventFieldValue(event, "Timestamp")))
        

        if "syscall_entry" in event.getName():
            num_of_func_callstack = int(getEventFieldValue(event, "context.__callstack_user_length"))
            if num_of_func_callstack == 0:
                continue
            tidpid_str = event.getName().replace("syscall_entry","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            start_time_str = str(getEventFieldValue(event, "Timestamp"))
            start_time = time_str_to_int(start_time_str)
            callstack = getEventFieldValue(event, "context._callstack_user")
            callstack_last_function = str(hex(callstack[len(callstack)-1]))
            
            syscall_entry_list.append([event.getName().replace("syscall_entry",""),tidpid_str,-1.0,callstack_last_function])
            syscall_entry_Timestamp_list.append(start_time)

            if callstack_last_function not in unique_functions:
                unique_functions.append(callstack_last_function)
        
        elif "syscall_exit" in event.getName():
            tidpid_str = event.getName().replace("syscall_exit","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            for x in range(len(syscall_entry_list)-1,-1,-1):
                if syscall_entry_list[x][1] == tidpid_str:
                    timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
                    period = (timestamp - syscall_entry_Timestamp_list[x]) * 1000
                    syscall_entry_list[x][2] = period
                    break
        
        else:
            continue
        

   
    function_syscalls_period = [[]] * len(unique_functions)

    for i in range(len(unique_functions)):
        for entries in syscall_entry_list:
            if entries[3] == unique_functions[i]:
                function_syscalls_period[i].append(entries[2])

    

    
    

    #define thresholds here
    a = 1 #forget
    b = 50 #success
    c = 100 #fail

    functions_status = [[0]*2]*len(unique_functions)

    for i in range(len(function_syscalls_period)):
        for period in function_syscalls_period[i]:
            if period > c:
                functions_status[i][1] = functions_status[i][1] + 1
            elif period > b:
                continue
            elif period > a:
                functions_status[i][0] = functions_status[i][0] + 1
            else:
                continue
    


    f = open("csv\\"+"syscalls.csv", "w")
    f.write("Function,Total_Syscalls_Success,Total_Syscalls_Failed\n")

    for i in range(len(unique_functions)):
        #print(function_syscalls_period[i])
        string_builder = unique_functions[i]+","+str(functions_status[i][0])+","+str(functions_status[i][1])+"\n"
        f.write(string_builder)
    
    f.close()
    
    # print("d1")
    # for ele in syscall_entry_list:
    #     f.write(str(ele[0])+","+str(ele[3])+","+str(ele[2])+"\n")
    #     if ele[0] not in unique_syscalls:
    #         unique_syscalls.append(ele[0])
    # f.close()

    # print("d2")
    # for ele in unique_syscalls:
    #     f = open("csv\\"+ele+".csv", "w")
    #     f.write("Callstack,Period\n")
    #     f.close()

    # print("d3")
    # for ele in unique_syscalls:
    #     f = open("csv\\"+ele+".csv", "a")
    #     for ele_all in syscall_entry_list:
    #         if ele_all[0] == ele:
    #             f.write(str(ele_all[3])+","+str(ele_all[2])+"\n")
    #     f.close()

    # print("d4")
    # Done parsing the events, close the state system at the time of the last event, it needs to be done manually otherwise the state system will still be waiting for values and will not be considered finished building
    if not(event is None):
        ss.closeHistory(event.getTimestamp().toNanos())
    # print("d5")


runAnalysis()

print("End")
