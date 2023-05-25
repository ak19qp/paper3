import re


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


tracefile = []
should_log = False # set only this to true to log

start_logging = False

#change this file name to the perf script output file name
filename = "test.txt"

with open(filename) as file:

    mode_enter = False

    callstack_string_builder = "-"

    

    for line in file:
        tracefile.append(line)

        
        line = line.replace("\n","")
        line = line.strip()

        
        
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
            if "-"+match.group(1)+"-" not in unique_functions:
                unique_functions.append("-"+match.group(1)+"-")

            if start_logging:
                a.write("\n")
                a.write("Stack mode:\n")
                a.write("line:\n")
                a.write(line+"\n")
                a.write("callstack_string_builder:\n")
                a.write(callstack_string_builder+"\n")

        
        


a.close()

function_periods = [[] * 2 for _ in range(len(unique_functions))]

print("Started sorting...")

index_of_max_len_period_function = 0

index_counter = -1
for function in unique_functions:
    index_counter = index_counter + 1
    for i in range(len(syscall)):
        if function in syscall[i][6]:
            function_periods[index_counter].append(syscall[i][5])
            function_periods_executor[index_counter].append(False)

            if len(function_periods[index_counter]) > len(function_periods[index_of_max_len_period_function]):
                index_of_max_len_period_function = index_counter





print("Writing to file...")


f = open("stats_with_addr.csv", "w")

f.write(','.join(unique_functions)+"\n")


for i in range(len(index_of_max_len_period_function)):

    string_builder = ""

    for j in range(len(unique_functions)):

        if(len(function_periods[j]) > i):

            string_builder = string_builder + str(function_periods[j][i]) + ","

        else:
            string_builder = string_builder + ","

    string_builder = string_builder[0:-1] + "\n"

    f.write(string_builder)



f.close()

print("Writing to file complete.")


# print("Converting addr to names...")



        

# a = open("stats_with_name.csv", "w")

# with open("stats_with_addr.csv") as file:


#     for line in file:

#         replace = line.split(",")[0]
#         addr = " "+line.split(",")[0]+" "

#         for trace in tracefile:
#             if addr in trace:
#                 addr = trace.replace(addr,"").split("(/",1)[0].strip().split("+0x",1)[0].replace("\n","")
#                 break
        
#         if "unknown" in addr:
#             addr = replace + " | " + addr
#         a.write(line.replace(replace+",", '"'+addr+'",', 1))

# a.close()


print("All complete!")
