import re
import statistics
import math
import time


print("Start")


syscall = []



callstack = []
period = []

unique_functions = []




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

    callstack_string_builder = "---"

    

    for line in file:

        

        
        line = line.replace("\n","")
        line = line.strip()
        
        
        if line == "":
            if start_logging:
                a.write("\nEmpty line\n")
            if callstack_string_builder != "---" and mode_enter:
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                syscall[-1][6] = callstack_string_builder
                callstack_string_builder = "---"
            continue


        #enter
        if re.match(enter_pattern, line):
            if should_log:
                start_logging = True

            mode_enter = True
            if callstack_string_builder != "---":
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                

            match = re.match(enter_pattern, line)
            process_name = match.group(1)
            pid = match.group(2)
            cpu_id = match.group(3)
            timestamp = float(match.group(4))
            syscall_name = match.group(5)
            

            callstack_string_builder = "---syscall_"+syscall_name+"---"

            if "---syscall_"+syscall_name+"---" not in unique_functions:
                unique_functions.append("---syscall_"+syscall_name+"---")

            syscall.append([process_name,pid,cpu_id,timestamp,syscall_name,0.0,"---",-1.0])
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
            if callstack_string_builder != "---":
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                callstack_string_builder = "---"
            
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
            #match = re.search(r'^([0-9a-f]+)\s.*$', line)
            funcname = line.split(" ")[1].split("+0x",1)[0]

            callstack_string_builder = callstack_string_builder + funcname + "---"

            if "---"+funcname+"---" not in unique_functions:
                unique_functions.append("---"+funcname+"---")

            if start_logging:
                a.write("\n")
                a.write("Stack mode:\n")
                a.write("line:\n")
                a.write(line+"\n")
                a.write("callstack_string_builder:\n")
                a.write(callstack_string_builder+"\n")


a.close()

print("Reading complete!")

#indegree, outdegree, Degree, weighted indegree, weighted outdegree, Weighted Degree, Authority, Hub, pageranks
unique_functions_weights = [0.0] * len(unique_functions)



print("Reading gephi data...")

gephi_header=[]
with open("gephi.csv") as file:
    header_ignore = True
    for line in file:
        if header_ignore:
            line = line.replace("\n","")
            gephi_header = line.split(",")
            header_ignore = False
            continue

        line = line.replace("\n","")

        func_data = line.split(",")

        for i in range(len(unique_functions)):
            if unique_functions[i] == "---"+func_data[0]+"---":
                unique_functions_weights[i] = [float(p) for p in func_data[1:]]
                break
                



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
            tempstore = syscall[i][6].split("---")
            if len(tempstore) > 2 and "---"+tempstore[2]+"---" in function:
                function_periods_executor[index_counter][-1] = True
            elif "---"+tempstore[1]+"---" in function:
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

functions_status_fp_and_fpo_storage = [ [0] * 2 for _ in range(len(unique_functions))]

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

                functions_status_fp_and_fpo_storage[i][0] = functions_status_fp_and_fpo_storage[i][0] + 1
                functions_status_fp_and_fpo_storage[i][1] = functions_status_fp_and_fpo_storage[i][1] + 1
            else:
                functions_status_fp_and_fpo[i][1] = functions_status_fp_and_fpo[i][1] + 1

                functions_status_fp_and_fpo_storage[i][1] = functions_status_fp_and_fpo_storage[i][1] + 1
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



for x in range(len(unique_functions_weights[0])):

    for i in range(len(functions_status_fp_and_fpo)):
        try:
            functions_status_fp_and_fpo[i][0] = functions_status_fp_and_fpo_storage[i][0] * unique_functions_weights[i][x]
            functions_status_fp_and_fpo[i][1] = functions_status_fp_and_fpo_storage[i][1] * unique_functions_weights[i][x]
        except:
            functions_status_fp_and_fpo[i][0] = functions_status_fp_and_fpo_storage[i][0] * 0.0
            functions_status_fp_and_fpo[i][1] = functions_status_fp_and_fpo_storage[i][1] * 0.0



    print("Writing to file"+str(x)+"...")

    a = open("log2.txt", "w")

    f = open("newwithweights"+str(x)+".csv", "w")
    f.write(gephi_header[x+"\n"])
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

        


        string_builder = unique_functions[i].replace("---","")+","+str(len(function_periods[i]))+","+str(functions_status[i][0])+","+str(functions_status[i][1])+","+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+","+str(failure_p)+","+str(context_p)+","+str(increase_p)+","+str(importance_p)+"\n"
        f.write(string_builder)
        
    a.close()
    f.close()

    print("Writing to file complete.")





print("All complete!")
