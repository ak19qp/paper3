import re
import statistics
import math
import time


print("Start")


syscall = []



callstack = []
period = []

unique_functions = []
tracefile = []


enter_pattern = r'^(.+?)\s+(\d+)\s+\[(\d+)\]\s+(\d+\.\d+).*syscalls:sys_enter_(.*?):'
exit_pattern = r'^(.+?)\s+(\d+)\s+\[(\d+)\]\s+(\d+\.\d+).*syscalls:sys_exit_(.*?):'
stack_pattern = r'^([0-9a-f]+)\s.*$'


# stack_pattern1 = r"\b([a-zA-Z:_]+)::[a-zA-Z0-9_]+\b"
# stack_pattern2 = r'\s([^\s]+)\+\d+'


print("Reading from file...")


a = open("log.txt", "w")



should_log = False # set only this to true to log

start_logging = False

#change this file name to the perf script output file name
with open("test.txt") as file:

    mode_enter = False

    callstack_string_builder = "-"

    

    for line in file:

        

        
        line = line.replace("\n","")
        line = line.strip()

        tracefile.append(line)
        
        
        if line == "":
            if start_logging:
                a.write("\nEmpty line\n")
            if callstack_string_builder != "-" and mode_enter:
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                syscall[-1][6] = callstack_string_builder
                callstack_string_builder = "-"
            continue


        #enter
        if re.match(enter_pattern, line):
            if should_log:
                start_logging = True

            mode_enter = True
            if callstack_string_builder != "-":
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                callstack_string_builder = "-"

            match = re.match(enter_pattern, line)
            process_name = match.group(1)
            pid = match.group(2)
            cpu_id = match.group(3)
            timestamp = float(match.group(4))
            syscall_name = match.group(5)

            syscall.append([process_name,pid,cpu_id,timestamp,syscall_name,0.0,"-",-1.0])
            period.append(0.0)

            if start_logging:
                a.write("\n")
                a.write("Enter mode:\n")
                a.write("line:\n")
                a.write(line+"\n")
                a.write("syscall:\n")
                a.write(str(syscall[-1])+"\n")
                a.write("period:\n")
                a.write(str(period[-1])+"\n")
            
            
        #exit
        elif re.match(exit_pattern, line):
            mode_enter = False
            if callstack_string_builder != "-":
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                callstack_string_builder = "-"
            
            match = re.match(exit_pattern, line)
            process_name = match.group(1)
            pid = match.group(2)
            cpu_id = match.group(3)
            timestamp = float(match.group(4))
            syscall_name = match.group(5)

            for i in range(len(syscall)-1,-1,-1):
                if syscall[i][0] == process_name and syscall[i][1] == pid and syscall[i][2] == cpu_id and syscall[i][4] == syscall_name:
                    if syscall[i][3] <= timestamp:

                        syscall[i][5] = float((timestamp) - (syscall[i][3])) * 1000
                        syscall[i][7] = timestamp
                        period[i] = float((timestamp) - (syscall[i][3])) * 1000
                        break

            if start_logging:
                a.write("\n")
                a.write("Exit mode:\n")
                a.write("line:\n")
                a.write(line+"\n")
                a.write("syscall:\n")
                a.write(str(syscall[-1])+"\n")
                a.write("period:\n")
                a.write(str(period[-1])+"\n")
                a.write("Callstack:\n")
                a.write(str(callstack[-1])+"\n")
        
        #callstack
        elif mode_enter and re.search(r'^([0-9a-f]+)\s.*$', line):
            match = re.search(r'^([0-9a-f]+)\s.*$', line)
            callstack_string_builder = callstack_string_builder + match.group(1) + "-"

            if "-"+match.group(1)+"-" not in unique_functions and "unknown" not in line:
                unique_functions.append("-"+match.group(1)+"-")

            if start_logging:
                a.write("\n")
                a.write("Stack mode:\n")
                a.write("line:\n")
                a.write(line+"\n")
                a.write("callstack_string_builder:\n")
                a.write(callstack_string_builder+"\n")

        
        


a.close()


print("Writing the new thing...")

newthing = []

f = open("newthing_addr.csv", "w")
f.write("Id,Source,Target,Interval\n")
for i in range(len(syscall)):
    if period[i] == 0.0:
        continue
    pairs = syscall[i][6].split("-")[1:-1]
    pairs.append("syscall_"+syscall[i][4])

    for j in range(len(pairs)-1):
        str_opt = str(i)+","+pairs[j]+","+pairs[j+1]+","+str(period[i])+"\n"
        f.write(str_opt)
        newthing.append(str_opt)

f.close()


print("Converting newthing addr to names...")




last_find_index = 0


a = open("newthing_with_name.csv", "w")
a.write("Id,Source,Target,Interval\n")

idcounter = 0
for line in newthing:

    idcounter = idcounter + 1

    split_str = line.split(",")
    

   
    addr1 = split_str[0]
    addr2 = split_str[1]

    name1 = addr1
    name2 = addr2

    n1f = False
    n2f = False
    zz = len(tracefile)
    for i in range(last_find_index,zz,1):

       

        trace = tracefile[i].split(" ")

      
        if len(trace) < 2:
            continue

        

        name = trace[1].split("+0x",1)[0]

  
        if not n1f and addr1 in trace[0]:
            name1 = name
           
            if name1 == "unknown":
                name1 = addr1
            n1f = True

        if not n2f and "syscall_" in addr2:
            name2 = addr2
          
            n2f = True
        else:
            if not n2f and addr2 in trace[0]:
                name2 = name
               
                if name2 == "unknown":
                    name2 = addr2
                n2f = True
        
        if n1f and n2f:
            last_find_index = i - 1
            break

        


    str_builder = '"'+name1+'","'+name2+'",'+split_str[2]

    a.write(str(idcounter)+","+str_builder)


a.close()

print("new thing done")
print("back to old things...")

function_periods = [[] * 2 for _ in range(len(unique_functions))]
function_periods_executor = [[] * 2 for _ in range(len(unique_functions))]

print("Started sorting...")


index_counter = -1
for function in unique_functions:
    index_counter = index_counter + 1
    for i in range(len(syscall)):
        if function in syscall[i][6]:
            function_periods[index_counter].append(syscall[i][5])
            function_periods_executor[index_counter].append(False)
            if "-"+syscall[i][6].split("-")[-2]+"-" in function:
                function_periods_executor[index_counter][-1] = True








print("Checking against thresholds...")


mean_stdev = [ [0.0] * 2 for _ in range(len(unique_functions))]
for i in range(len(unique_functions)):

    mean = 0.0
    stdev = 0.0

    try:
        mean = statistics.mean(function_periods[i])
        stdev = statistics.stdev(function_periods[i])
    except:
        mean = 0.0
        stdev = 0.0

    mean_stdev[i][0] = mean
    mean_stdev[i][0] = stdev




functions_status = [ [0] * 2 for _ in range(len(unique_functions))]

functions_status_sp_and_spo = [ [0] * 2 for _ in range(len(unique_functions))]
functions_status_fp_and_fpo = [ [0] * 2 for _ in range(len(unique_functions))]

success = 0
fail = 0
forget = 0
total = 0

for i in range(len(unique_functions)):

    for j in range(len(function_periods[i])):
        period = function_periods[i][j]
        if period >= (mean_stdev[i][0] + mean_stdev[i][1]):
            functions_status[i][1] += 1
            fail = fail + 1
            if function_periods_executor[i][j]:
                functions_status_fp_and_fpo[i][0] = functions_status_fp_and_fpo[i][0] + 1
                functions_status_fp_and_fpo[i][1] = functions_status_fp_and_fpo[i][1] + 1
            else:
                functions_status_fp_and_fpo[i][1] = functions_status_fp_and_fpo[i][1] + 1
            # print("Fail")
        # elif period <= (mean_stdev[i][0] - (2*mean_stdev[i][1])):
        #     forget = forget + 1
        #     # print("Forget")
        #     continue
        else:
            functions_status[i][0] += 1
            success = success + 1
            if function_periods_executor[i][j]:
                functions_status_sp_and_spo[i][0] = functions_status_sp_and_spo[i][0] + 1
                functions_status_sp_and_spo[i][1] = functions_status_sp_and_spo[i][1] + 1
            else:
                functions_status_sp_and_spo[i][1] = functions_status_sp_and_spo[i][1] + 1
            # print("Success")
        

total = success + fail + forget

print("Writing to file...")

a = open("log2.txt", "w")

f = open("stats_with_addr.csv", "w")
f.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Min,Max,Average,Stdev,Failure,Context,Increase,Importance\n")
for i in range(len(unique_functions)):

    mean = 0.0
    stdev = 0.0
    minimum = 0.0
    maximum = 0.0
    try:
        mean = statistics.mean(function_periods[i])
        stdev = statistics.stdev(function_periods[i])
    except:
        mean = 0.0
        stdev = 0.0

    
    try:
        minimum = min(function_periods[i])
        maximum = max(function_periods[i])
    except:
        minimum = 0.0
        maximum = 0.0
    

    if start_logging:
        a.write("\nFunc: "+unique_functions[i]+"\n"+str(function_periods[i])+"\nMin:"+str(minimum)+"\nMax:"+str(maximum)+"\nMean:"+str(mean)+"\nStdev:"+str(stdev)+"\n")
    

    period_in_str = ' | '.join(str(f) for f in function_periods[i]).strip().replace("\n","")
    period_in_str = '"'+period_in_str+'"'


    failure_p = 0.0
    context_p = 0.0
    increase_p = 0.0
    importance_p = 0.0

    try:
        failure_p = functions_status_fp_and_fpo[i][0] / (functions_status_sp_and_spo[i][0] + functions_status_fp_and_fpo[i][0])
    except:
        failure_p = 0.0
    
    try:
        context_p = functions_status_fp_and_fpo[i][1] / (functions_status_sp_and_spo[i][1] + functions_status_fp_and_fpo[i][1])
    except:
        context_p = 0.0
    
    try:
        increase_p = failure_p - context_p
    except:
        increase_p = 0.0
    
    try:
        importance_p = 2 / ((1/increase_p)+(1/(math.log(functions_status_fp_and_fpo[i][0])/math.log(fail))))
    except:
        importance_p = 0.0

    


    string_builder = unique_functions[i].replace("-","")+","+str(len(function_periods[i]))+","+str(functions_status[i][0])+","+str(functions_status[i][1])+","+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+","+str(failure_p)+","+str(context_p)+","+str(increase_p)+","+str(importance_p)+"\n"
    f.write(string_builder)
    
a.close()
f.close()

print("Writing to file complete.")


print("Converting addr to names...")





a = open("stats_with_name.csv", "w")

with open("stats_with_addr.csv") as file:

    is_heading = True
    for line in file:
        if is_heading:
            is_heading = False
            a.write(line)
            continue
        replace = line.split(",")[0]
        addr = " "+line.split(",")[0]+" "

        for trace in tracefile:
            if addr in trace:
                addr = trace.replace(addr,"").split("(/",1)[0].strip().split("+0x",1)[0].replace("\n","")
                break
        
        if "unknown" in addr:
            addr = replace + " | " + addr
        a.write(line.replace(replace+",", '"'+addr+'",', 1))

a.close()


print("All complete!")
