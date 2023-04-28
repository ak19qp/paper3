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


    block_getrq_list = []
    block_rq_insert_list = []
    block_rq_issue_list = []
    block_rq_complete_list = []
    sched_waking_list = []
    sched_switch_list = []
  
    
    syscall_entry_list = []
    syscall_entry_Timestamp_list  = []

    unique_syscalls = []

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
        
        if event.getName() == "block_getrq":
            num_of_func_callstack = int(getEventFieldValue(event, "context.__callstack_user_length"))
            if num_of_func_callstack == 0:
                continue
            devsectortidpid = str(getEventFieldValue(event, "dev")) + str(getEventFieldValue(event, "sector")) + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
            callstack = ""
            for ele in getEventFieldValue(event, "context._callstack_user"):
                callstack = callstack + str(hex(ele)) + " "
            block_getrq_list.append([devsectortidpid,timestamp,callstack.rstrip()])


        elif event.getName() == "block_rq_insert":
            devsectortidpid = str(getEventFieldValue(event, "dev")) + str(getEventFieldValue(event, "sector")) + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
            found = False
            track = len(block_getrq_list)
            for i in range(len(block_getrq_list)-1,-1,-1):
                track = track-1
                if devsectortidpid == block_getrq_list[i][0] and timestamp >= block_getrq_list[i][1]:
                    found = True
                    break
            if found:
                callstack = ""
                for ele in getEventFieldValue(event, "context._callstack_user"):
                    callstack = callstack + str(hex(ele)) + " "
                block_rq_insert_list.append([track,devsectortidpid,timestamp,callstack.rstrip()])
            else:
                continue
            

        elif event.getName() == "block_rq_issue":
            devsectortidpid = str(getEventFieldValue(event, "dev")) + str(getEventFieldValue(event, "sector")) + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
            devsector = str(getEventFieldValue(event, "dev")) + str(getEventFieldValue(event, "sector"))
            timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
            found = False
            track = len(block_rq_insert_list)
            for i in range(len(block_rq_insert_list)-1,-1,-1):
                track = track-1
                if devsectortidpid == block_rq_insert_list[i][1] and timestamp >= block_rq_insert_list[i][2]:
                    found = True
                    break
            if found:
                callstack = ""
                for ele in getEventFieldValue(event, "context._callstack_user"):
                    callstack = callstack + str(hex(ele)) + " "
                block_rq_issue_list.append([track,devsector,timestamp,callstack.rstrip()])
            else:
                continue


        elif event.getName() == "block_rq_complete":
            devsector = str(getEventFieldValue(event, "dev")) + str(getEventFieldValue(event, "sector"))
            timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
            found = False
            track = len(block_rq_insert_list)
            for i in range(len(block_rq_issue_list)-1,-1,-1):
                track = track-1
                if devsector == block_rq_issue_list[i][1] and timestamp >= block_rq_issue_list[i][2]:
                    found = True
                    break
            if found:
                callstack = ""
                for ele in getEventFieldValue(event, "context._callstack_user"):
                    callstack = callstack + str(hex(ele)) + " "
                block_rq_complete_list.append([track,devsector,timestamp,callstack.rstrip()])
            else:
                continue


        elif event.getName() == "sched_waking":
            tid = str(getEventFieldValue(event, "tid"))
            if tid == "":
                continue
            else:
                timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
                callstack = ""
                for ele in getEventFieldValue(event, "context._callstack_user"):
                    callstack = callstack + str(hex(ele)) + " "
                sched_waking_list.append([tid,timestamp,callstack.rstrip()])

        
        elif event.getName() == "sched_switch":
            next_tid = str(getEventFieldValue(event, "next_tid"))
            found = False
            timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
            track = len(sched_waking_list)
            for i in range(len(sched_waking_list)-1,-1,-1):
                track = track - 1
                if next_tid == sched_waking_list[i][0] and timestamp >= sched_waking_list[i][1]:
                    found = True
                    break
            if found:
                callstack = ""
                for ele in getEventFieldValue(event, "context._callstack_user"):
                    callstack = callstack + str(hex(ele)) + " "
                sched_switch_list.append([track,timestamp,callstack.rstrip()])
            else:
                continue

        # elif "syscall_entry" in event.getName():
        #     num_of_func_callstack = int(getEventFieldValue(event, "context.__callstack_user_length"))
        #     if num_of_func_callstack == 0:
        #         continue
        #     tid_pid_str = event.getName().replace("syscall_entry","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
        #     start_time_str = str(getEventFieldValue(event, "Timestamp"))
        #     start_time = time_str_to_int(start_time_str)
        #     callstack = ""
        #     for ele in getEventFieldValue(event, "context._callstack_user"):
        #         callstack = callstack + str(hex(ele)) + " "
        #     syscall_entry_list.append([event.getName().replace("syscall_entry",""),tid_pid_str,-1.0,callstack])
        #     syscall_entry_Timestamp_list.append(start_time)
        
        # elif "syscall_exit" in event.getName():
        #     tid_pid_str = event.getName().replace("syscall_exit","") + str(getEventFieldValue(event, "TID")) + str(getEventFieldValue(event, "PID"))
        #     for x in range(len(syscall_entry_list)-1,-1,-1):
        #         if syscall_entry_list[x][1] == tid_pid_str:
        #             timestamp = time_str_to_int(str(getEventFieldValue(event, "Timestamp")))
        #             period = (timestamp - syscall_entry_Timestamp_list[x]) * 1000000
        #             syscall_entry_list[x][2] = period
        #             break
        

    f = open("csv\\"+"block_rq.csv", "w")
    f.write("Getrq_Insert_Period,Insert_Issue_Period,Issue_Complete_Period,Getrq_Callstack\n")

    for i in block_rq_complete_list:
        track1 = i[0]
        Issue_Complete = str((i[2] - block_rq_issue_list[track1][2])*1000000)
        track2 = block_rq_issue_list[track1][0]
        Insert_Issue = str((block_rq_issue_list[track1][2] - block_rq_insert_list[track2][2])*1000000)
        track3 = block_rq_insert_list[track2][0]
        Getrq_Insert = str((block_rq_insert_list[track2][2] - block_getrq_list[track3][1])*1000000)
        Callstack = block_getrq_list[track3][2]
        f.write(Getrq_Insert+","+Insert_Issue+","+Issue_Complete+","+Callstack+"\n")

    f.close()
    
    # sched_waking_list.append([tid,timestamp,callstack])
    # sched_switch_list.append([track,timestamp,callstack])

    f = open("csv\\"+"sched.csv", "w")
    f.write("Waking_Switch_Period,Waking_Callstack,Switch_Callstack\n")
    for i in sched_switch_list:
        track1 = i[0]
        Waking_Switch = str((i[1] - sched_waking_list[track1][1])*1000000)
        Waking_Callstack = sched_waking_list[track1][2]
        Switch_Callstack = i[2]
        f.write(Waking_Switch+","+Waking_Callstack+","+Switch_Callstack+"\n")

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


runAnalysis(1000)

print("End")
