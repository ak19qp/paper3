# data must be sorted already, use excel to do it and then get rid of the unnecessary data.

import re
import statistics
import math

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

tracefile = []


#change this file name to the perf script output file name
file_name = "raw data of case study 2.txt"
sorted_file_name="stats_with_addr_500_cutoff.csv"
with open(file_name) as file:

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

print("Reading sorted file...")


sorted_addr = []
sorted_addr_increase = []
with open(sorted_file_name) as file:

    for line in file:
        line = line.replace("\n","")
        line = line.strip()
        addr_data = line.split(",")
        sorted_addr.append(addr_data[0])
        sorted_addr_increase.append(addr_data[1])




print("Started filtering paths...")


threshold = 19.2
paths_to_print = []
paths_to_print_increase_values = []
for i in range(len(syscall)):
    if syscall[i][5] >= threshold:
        for j in range(len(sorted_addr)):
            if sorted_addr[j] in syscall[i][6]:
                paths_to_print.append(syscall[i][6])
                paths_to_print_increase_values.append(sorted_addr_increase[j])



print("Writing to file...")


f = open("paths_addr.csv", "w")
f.write("Max_Increase,Func_Path\n")
for i in range(len(paths_to_print)):
    f.write(paths_to_print_increase_values[i]+","+paths_to_print[i]+"\n")
    

f.close()

print("Writing to file complete.")


print("Converting addr to names...")




        


a = open("paths_names.csv", "w")

with open("paths_addr.csv") as file:

    is_heading = True
    for line in file:
        if is_heading:
            is_heading = False
            a.write(line)
            continue
        increase = line.split(",")[0]
        addr = line.split(",")[1].split("-")[1:-1]

        last_index = 0
        for i in range(len(addr)):
            for j in range(last_index,len(tracefile),1):
                if addr[i] in tracefile[j]:
                    addr[i] = tracefile[j].replace(addr[i],"").split("(/",1)[0].strip().split("+0x",1)[0].replace("\n","")
                    last_index = j
                    break

        addr_to_write = '>>>'.join(addr)
        a.write(increase + "," + '"'+addr_to_write+'"\n')

a.close()


print("All complete!")
