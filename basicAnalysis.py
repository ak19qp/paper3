# load proper Trace Compass modules
loadModule('/TraceCompass/Analysis');
loadModule('/TraceCompass/Trace');
loadModule('/TraceCompass/View');
loadModule('/TraceCompass/DataProvider');

from py4j.java_gateway import JavaClass
from datetime import datetime


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
def runAnalysis():
    # Get the event iterator for the trace
    iter = analysis.getEventIterator()
   
    # Parse all events
    event = None


    block_rq_sector_list = []
    block_rq_Timestamp_list = []
    block_rq_Timestamp_list_str = []
    callstack_list_block_rq = []

    block_rq_complete_sector_list = []
    block_rq_complete_Timestamp_list = []
    block_rq_complete_Timestamp_list_str = []


    syscall_entry_list = []
    syscall_entry_Timestamp_list  = []

    
    while iter.hasNext():
        # The python java gateway keeps a reference to the Java objects it sends to python. To avoid OutOfMemoryException, they need to be explicitly detached from the gateway when not needed anymore
        if not(event is None):
            gateway.detach(event)
        
        event = iter.next();
        

        if event.getName() == "block_getrq":
            num_of_func_callstack = int(getEventFieldValue(event, "context.__callstack_user_length"))
            if num_of_func_callstack == 0:
                continue
            sector = str(getEventFieldValue(event, "sector"))
            start_time_str = str(getEventFieldValue(event, "Timestamp"))
            callstack = ""
            for ele in getEventFieldValue(event, "context._callstack_user"):
                callstack = callstack + str(hex(ele)) + " "
            start_time = time_str_to_int(start_time_str)
            block_rq_sector_list.append(sector)
            block_rq_Timestamp_list.append(start_time)
            block_rq_Timestamp_list_str.append(start_time_str)
            callstack_list_block_rq.append(callstack)
        
        elif event.getName() == "block_rq_complete":
            sector = str(getEventFieldValue(event, "sector"))
            start_time_str = str(getEventFieldValue(event, "Timestamp"))
            start_time = time_str_to_int(start_time_str)
            if sector not in block_rq_sector_list:
                continue
            block_rq_complete_sector_list.append(sector)
            block_rq_complete_Timestamp_list.append(start_time)
            block_rq_complete_Timestamp_list_str.append(start_time_str)

        elif "syscall_entry" in event.getName():
            num_of_func_callstack = int(getEventFieldValue(event, "context.__callstack_user_length"))
            if num_of_func_callstack == 0:
                continue
            tid_pid_str = event.getName().replace("syscall_entry","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            start_time_str = str(getEventFieldValue(event, "Timestamp"))
            start_time = time_str_to_int(start_time_str)
            callstack = ""
            for ele in getEventFieldValue(event, "context._callstack_user"):
                callstack = callstack + str(hex(ele)) + " "
            syscall_entry_list.append([event.getName().replace("syscall_entry",""),tid_pid_str,-1.0,callstack])
            syscall_entry_Timestamp_list.append(start_time)
        
        elif "syscall_exit" in event.getName():
            tid_pid_str = event.getName().replace("syscall_exit","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            for x in range(len(syscall_entry_list)-1,-1,-1):
                if syscall_entry_list[x][1] == tid_pid_str:
                    timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
                    period = timestamp - syscall_entry_Timestamp_list[x]
                    syscall_entry_list[x][2] = period
                    break
        


            
        
    
    f = open("block_requests.csv", "w")
    f.write("Callstack,Period\n")
    

    for i in range(len(block_rq_sector_list)):
        output_str = "Sector: " + block_rq_sector_list[i]
        if block_rq_sector_list[i] not in block_rq_complete_sector_list:
            output_str = output_str + " : Incomplete/Blocked" + " | User Callstack: " + callstack_list_block_rq[i]
            f.write(callstack_list_block_rq[i]+",-1.0\n")
        else:
            indices = [ii for ii, x in enumerate(block_rq_complete_sector_list) if x == block_rq_sector_list[i]]
            index = 0
            for j in indices:
                if block_rq_complete_Timestamp_list[j] > block_rq_Timestamp_list[i]:
                    index = j
                    break
                else:
                    index = -1
            
            if index == -1:
                output_str = output_str + " | Incomplete/Blocked" + " | User Callstack: " + callstack_list_block_rq[i]
                f.write(callstack_list_block_rq[i]+",-1.0\n")
            else:
                period = block_rq_complete_Timestamp_list[index] - block_rq_Timestamp_list[i]
                output_str = output_str + " | Block Period: " + str(period) + " | User Callstack: " + callstack_list_block_rq[i]
                f.write(callstack_list_block_rq[i]+","+str(period)+"\n")
                            
           
        print(output_str)

    f.close()
    
    f = open("syscalls.csv", "w")
    f.write("Syscall,Callstack,Period\n")

    syscall_entry_list.append([event.getName(),tid_pid_str,-1.0,callstack])
    for ele in syscall_entry_list:
        f.write(str(ele[0])+","+str(ele[3])+","+str(ele[2])+"\n")
    
    f.close()

    # Done parsing the events, close the state system at the time of the last event, it needs to be done manually otherwise the state system will still be waiting for values and will not be considered finished building
    if not(event is None):
        ss.closeHistory(event.getTimestamp().toNanos())

runAnalysis()

print("End")
