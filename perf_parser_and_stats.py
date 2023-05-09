import re
import statistics

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


with open("test.txt") as file:

    mode_enter = False

    callstack_string_builder = "-"

    start_logging = False

    for line in file:

        
        line = line.replace("\n","")
        line = line.strip()

        
        
        if line == "":
            a.write("\nEmpty line\n")
            if callstack_string_builder != "-" and mode_enter:
                callstack_string_builder = callstack_string_builder.strip()
                callstack.append(callstack_string_builder)
                syscall[-1][6] = callstack_string_builder
                callstack_string_builder = "-"
            continue


        #enter
        if re.match(enter_pattern, line):
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

            
            a.write("\n")
            a.write("Stack mode:\n")
            a.write("line:\n")
            a.write(line+"\n")
            a.write("callstack_string_builder:\n")
            a.write(callstack_string_builder+"\n")

        
        


a.close()

function_periods = [[] * 2 for _ in range(len(unique_functions))]


print("Started sorting...")


index_counter = -1
for function in unique_functions:
    index_counter = index_counter + 1
    for i in range(len(syscall)):
        if function in syscall[i][6]:
            function_periods[index_counter].append(syscall[i][5])



print("Checking against thresholds...")

#define thresholds here in ms
a = 0.01 #forget
b = 5 #success
c = 10 #fail

functions_status = [ [0] * 2 for _ in range(len(unique_functions))]

success = 0
fail = 0
forget = 0
total = 0
for i in range(len(unique_functions)):

    for period in function_periods[i]:
        if period > c:
            functions_status[i][1] += 1
            fail = fail + 1
            # print("Fail")
        elif period > b:
            forget = forget + 1
            # print("Forget")
            continue
        elif period > a:
            functions_status[i][0] += 1
            success = success + 1
            # print("Success")
        else:
            forget = forget + 1
            # print("Forget")
            continue

total = success + fail + forget

print("Writing to file...")

a = open("log2.txt", "w")

f = open("stats_with_addr.csv", "w")
f.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Min,Max,Average,Stdev\n")
for i in range(len(unique_functions)):
    #print(function_syscalls_period[i])

    mean = 0.0
    stdev = 0.0
    minimum = 0.0
    maximum = 0.0
    try:
        # mean = sum(function_periods[i]) / len(function_periods[i])
        # numerator = 0
        # for num in function_periods[i]:
        #     numerator += (num - mean) ** 2
        # stdev = (numerator / (len(function_periods[i]) - 1)) ** 0.5

        mean = statistics.mean(function_periods[i])
        stdev = statistics.stdev(function_periods[i])
    except:
        # print("error calculating mean and stdev for:")
        # print(function_periods[i])
        mean = 0.0
        stdev = 0.0

    
    try:
        minimum = min(function_periods[i])
        maximum = max(function_periods[i])
    except:
        minimum = 0.0
        maximum = 0.0
    

    
    a.write("\nFunc: "+unique_functions[i]+"\n"+str(function_periods[i])+"\nMin:"+str(minimum)+"\nMax:"+str(maximum)+"\nMean:"+str(mean)+"\nStdev:"+str(stdev)+"\n")
    

    period_in_str = ' | '.join(str(f) for f in function_periods[i]).strip().replace("\n","")
    period_in_str = '"'+period_in_str+'"'
    string_builder = unique_functions[i].replace("-","")+","+str(len(function_periods[i]))+","+str(functions_status[i][0])+","+str(functions_status[i][1])+","+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+"\n"
    f.write(string_builder)
    
a.close()
f.close()

print("Writing to file complete.")


print("Converting addr to names...")


tracefile = []

with open("test.txt") as file:

    for line in file:
        tracefile.append(line)


a = open("stats_with_name.csv", "w")
a.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Min,Max,Average,Stdev\n")

with open("stats_with_addr.csv") as file:

    skip = True
    for line in file:
        if skip:
            skip = False
            continue
        replace = line.split(",")[0]
        addr = " "+line.split(",")[0]+" "

        for trace in tracefile:
            if addr in trace:
                addr = trace.replace(addr,"").split("(/",1)[0].strip().split("+0x",1)[0]
                break
        
        if "unknown" in addr:
            addr = replace + " | " + addr
        a.write(line.replace(replace, '"'+addr+'"'))

a.close()


print("All complete!")
