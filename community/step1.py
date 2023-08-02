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
                callstack_string_builder = "---"

            match = re.match(enter_pattern, line)
            process_name = match.group(1)
            pid = match.group(2)
            cpu_id = match.group(3)
            timestamp = float(match.group(4))
            syscall_name = match.group(5)

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

            if "---"+funcname+"---" not in unique_functions and "unknown" not in line:
                unique_functions.append("---"+funcname+"---")

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

f = open("newthing.csv", "w")
f.write("Id,Source,Target,Interval\n")
for i in range(len(syscall)):
    if period[i] == 0.0:
        continue
    pairs = syscall[i][6].split("---")[1:-1]
    pairs.append("syscall_"+syscall[i][4])

    for j in range(len(pairs)-1):
        str_opt = str(i)+","+pairs[j]+","+pairs[j+1]+","+str(period[i])+"\n"
        f.write(str_opt)
        newthing.append(str_opt)

f.close()

print("new thing done")

print("All complete!")
