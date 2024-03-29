import bt2
import sys
import pandas as pd
import re
import statistics
import math

class EventList:

    function_address = []
    function_name = []
    func_set = set()
    gephi_headers = []
    threshold = 0

    def __init__(self, perf_file, procname, threshold):

        self.threshold = threshold
        self.eventsByCpuId = {}

        # perf_file = "/home/a/Desktop/c_code/bin/Debug/perf_output.txt"

        print("reading perf data...")

        with open(perf_file) as file:

            for line in file:
                
                line = line.replace("\n","")
                line = line.strip()

                # if "c_code" not in line:
                #     continue

                if procname not in line:
                    continue


                match = re.search(r'^([0-9a-f]+)\s.*$', line)
                if match:
                    addr = match.group(1)
                    if addr in self.function_address:
                        continue
                    funcname = line.split(" ")[1].split("+0x",1)[0]
                    if "unknown" in funcname:
                        continue
                    self.function_address.append(addr)
                    self.function_name.append(funcname)



    def no_of_ele(self):
        return(len(self.eventsByCpuId))

    def print_all(self):
        print(self.eventsByCpuId)


    def add(self, event):
        parts = event["name"].split("_")
        
        
        # event_type = parts[0]

        if parts[-1] != "entry" and parts[-1] != "exit":
            return

        event_name = event['name'].replace(parts[-1], "")
        event_is_entry = parts[-1] == "entry"

        # if event_type != "syscall":
        #     return


        # event_name = parts[2]
        # event_is_entry = parts[1] == "entry"

        
        
        if not event["cpu_id"] in self.eventsByCpuId:
            self.eventsByCpuId[event["cpu_id"]] = {}


        if not event_name in self.eventsByCpuId[event["cpu_id"]]:
            self.eventsByCpuId[event["cpu_id"]][event_name] = {
                "entries": [],
                "exits": [],
                "spans": [],
                "callstack_user": []
            }

        num_entries = len(self.eventsByCpuId[event["cpu_id"]][event_name]["entries"])
        num_exits = len(self.eventsByCpuId[event["cpu_id"]][event_name]["exits"])


        at_least_one_found = False
        first_one_found = False

        for j in range(len(event["callstack_user"])):
            for i in range(len(self.function_address)):
                if event["callstack_user"][j] == self.function_address[i]:
                    event["callstack_user"][j] = self.function_name[i]
                    at_least_one_found = True
                    break
            if j == 0 and at_least_one_found:
                first_one_found = True

        if at_least_one_found and not first_one_found:
            event["callstack_user"].pop(0)



                

        if num_entries == num_exits and event_is_entry and at_least_one_found:
            self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].append(event["timestamp"])
            self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].append(event["callstack_user"])
        elif num_entries > num_exits and not event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["exits"].append(event["timestamp"])
        elif num_entries > num_exits and event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].pop()
            self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].pop()
            if at_least_one_found:
                self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].append(event["timestamp"])
                self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].append(event["callstack_user"])
        elif num_entries < num_exits and event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["exits"].pop()



        num_exits = len(self.eventsByCpuId[event["cpu_id"]][event_name]["exits"])
        if num_entries != 0 and num_entries == num_exits and not event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["spans"].append(
                self.eventsByCpuId[event["cpu_id"]][event_name]["exits"][num_exits - 1] -
                self.eventsByCpuId[event["cpu_id"]][event_name]["entries"][num_entries - 1]
            )


    def final_non_weighted_calculations(self):
        functions = self.generate_functions()

        threshold = self.threshold

        for name in functions:
            for i in range(len(functions[name]["periods"])):
                if functions[name]["periods"][i] >= threshold:
                    functions[name]["fails"] += 1
                    if functions[name]["is_period_executor"][i]:
                        functions[name]["fail_present"] += 1
                        #functions[name]["fail_observed"] += 1
                    else:
                        functions[name]["fail_observed"] += 1
                else:
                    functions[name]["successes"] += 1
                    if functions[name]["is_period_executor"][i]:
                        functions[name]["success_present"] += 1
                        #functions[name]["success_observed"] += 1
                    else:
                        functions[name]["success_observed"] += 1

        i = 0

        for name in functions:
            try:
                failure = (functions[name]["fail_present"]) / (functions[name]["success_present"] + (functions[name]["fail_present"]))
                functions[name]["failure"] += [failure]
            except:
                functions[name]["failure"] += [0.0]
            
            try:
                context = (functions[name]["fail_observed"]) / (functions[name]["success_observed"] + (functions[name]["fails"]))
                functions[name]["context"] += [context]
            except:
                functions[name]["context"] += [0.0]
            
            try:
                increase = functions[name]["failure"][i] - functions[name]["context"][i]
                functions[name]["increase"] += [increase]
            except:
                functions[name]["increase"] += [0.0]
            
            try:
                importance = 2 / ((1/functions[name]["increase"][i])+(1/(math.log(functions[name]["fail_present"])/math.log(functions[name]["fails"]))))
                functions[name]["importance"] += [importance]
            except:
                functions[name]["importance"] += [0.0]


        f = open("regular_sd.csv", "w")
        f.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Failed(O),Failed(P),Success(O),Success(P),Min,Max,Average,Stdev,Failure,Context,Increase,Importance\n")

        for name in functions:
            minimum = min(functions[name]["periods"])
            maximum = max(functions[name]["periods"])
            mean = 0.0
            stdev = 0.0

            try:
                mean = statistics.mean(functions[name]["periods"])
                stdev = statistics.stdev(functions[name]["periods"])
            except:
                mean = float(functions[name]["periods"][0])
                stdev = 0.0

            string_builder = name+","+str(len(functions[name]["periods"]))+","+str(functions[name]["successes"])+","+str(functions[name]["fails"])+","
            string_builder = string_builder+str(functions[name]["fail_observed"])+","+str(functions[name]["fail_present"])+","+str(functions[name]["success_present"])+","+str(functions[name]["success_observed"])+","
            string_builder = string_builder+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+","+str(functions[name]["failure"][i])+","
            string_builder = string_builder+str(functions[name]["context"][i])+","+str(functions[name]["increase"][i])+","
            string_builder = string_builder+str(functions[name]["importance"][i])+"\n"

            f.write(string_builder)

        f.close()

        print("Writing to file complete.")

    def final_weighted_calculations(self):
        functions = self.generate_functions_with_weights()

        threshold = self.threshold

        for name in functions:
            for i in range(len(functions[name]["periods"])):
                if functions[name]["periods"][i] >= threshold:
                    functions[name]["fails"] += 1
                    if functions[name]["is_period_executor"][i]:
                        functions[name]["fail_present"] += 1
                        functions[name]["fail_observed"] += 1
                    else:
                        functions[name]["fail_observed"] += 1
                else:
                    functions[name]["successes"] += 1
                    if functions[name]["is_period_executor"][i]:
                        functions[name]["success_present"] += 1
                        functions[name]["success_observed"] += 1
                    else:
                        functions[name]["success_observed"] += 1

        for i in range(len(self.gephi_headers)):
            for name in functions:
                weight = functions[name]["weight"][i]

                try:
                    failure = (functions[name]["fail_present"] * weight) / (functions[name]["success_present"] + (functions[name]["fail_present"] * weight))
                    functions[name]["failure"] += [failure]
                except:
                    functions[name]["failure"] += [0.0]
                
                try:
                    context = (functions[name]["fail_present"] * weight) / (functions[name]["success_observed"] + (functions[name]["fail_observed"] * weight))
                    functions[name]["context"] += [context]
                except:
                    functions[name]["context"] += [0.0]
                
                try:
                    increase = functions[name]["failure"][i] - functions[name]["context"][i]
                    functions[name]["increase"] += [increase]
                except:
                    functions[name]["increase"] += [0.0]
                
                try:
                    importance = 2 / ((1/functions[name]["increase"][i])+(1/(math.log(functions[name]["fail_present"]*weight)/math.log(functions[name]["fails"]*weight))))
                    functions[name]["importance"] += [importance]
                except:
                    functions[name]["importance"] += [0.0]


        for i in range(len(self.gephi_headers)):

            f = open(self.gephi_headers[i]+".csv", "w")
            f.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Failed(O),Failed(P),Success(O),Success(P),Min,Max,Average,Stdev,Failure,Context,Increase,Importance\n")

            for name in functions:
                minimum = min(functions[name]["periods"])
                maximum = max(functions[name]["periods"])
                mean = 0.0
                stdev = 0.0

                try:
                    mean = statistics.mean(functions[name]["periods"])
                    stdev = statistics.stdev(functions[name]["periods"])
                except:
                    mean = float(functions[name]["periods"][0])
                    stdev = 0.0

                string_builder = name+","+str(len(functions[name]["periods"]))+","+str(functions[name]["successes"])+","+str(functions[name]["fails"])+","
                string_builder = string_builder+str(functions[name]["fail_observed"])+","+str(functions[name]["fail_present"])+","+str(functions[name]["success_present"])+","+str(functions[name]["success_observed"])+","
                string_builder = string_builder+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+","+str(functions[name]["failure"][i])+","
                string_builder = string_builder+str(functions[name]["context"][i])+","+str(functions[name]["increase"][i])+","
                string_builder = string_builder+str(functions[name]["importance"][i])+"\n"

                f.write(string_builder)

            f.close()

        print("Writing to file complete.")


    def generate_functions_with_weights(self):
        functions = self.generate_functions()

        gephi_file = "/home/a/Desktop/c_code/bin/Debug/gephi.csv"
        print("Reading gephi data...")
        with open(gephi_file) as file:
            header_ignore = True
            for line in file:
                if header_ignore:
                    line = line.replace("\n","")
                    self.gephi_headers = line.split(",")[1:]
                    header_ignore = False
                    continue

                line = line.replace("\n","")

                func_data = line.split(",")

                for name in functions:
                    if name == func_data[0]:
                        functions[name]["weight"] += [float(p) for p in func_data[1:]]
                        break

        print("removing functions with no weight data...")

        names_for_pop = []
        for name in functions:
            if len(functions[name]["weight"]) < 1:
                names_for_pop.append(name) 

        for name in names_for_pop:
            functions.pop(name)

        return functions


    def generate_functions(self):
        functions = {}
        eventsByName = self.flatten()

        for name in eventsByName:

            num_of_callstacks = len(eventsByName[name]["callstack_user"])

            for i in range(num_of_callstacks):
                is_first = True
                for func in eventsByName[name]["callstack_user"][i]:
                    if func in functions:
                        functions[func]["periods"] += [eventsByName[name]["spans"][i]]
                        functions[func]["is_period_executor"] += [is_first]
                    else:
                        functions[func] = {
                            "periods": [eventsByName[name]["spans"][i]],
                            "is_period_executor": [is_first],
                            "weight": [],
                            "fails": 0,
                            "fail_present": 0,
                            "fail_observed": 0,
                            "successes" : 0,
                            "success_present": 0,
                            "success_observed": 0,
                            "failure": [],
                            "context": [],
                            "increase": [],
                            "importance": []
                        }
                    is_first = False

        return functions



    def flatten(self):

        eventsByName = {}

        for cpu_id in self.eventsByCpuId:
            for name in self.eventsByCpuId[cpu_id]:
                if len(self.eventsByCpuId[cpu_id][name]["spans"]) > 0:
                    if name in eventsByName:
                        eventsByName[name]["entries"] = eventsByName[name]["entries"] + self.eventsByCpuId[cpu_id][name]["entries"]
                        eventsByName[name]["exits"] = eventsByName[name]["exits"] + self.eventsByCpuId[cpu_id][name]["exits"]
                        eventsByName[name]["spans"] = eventsByName[name]["spans"] + self.eventsByCpuId[cpu_id][name]["spans"]
                        eventsByName[name]["callstack_user"] = eventsByName[name]["callstack_user"] + self.eventsByCpuId[cpu_id][name]["callstack_user"]
                    else:
                        eventsByName[name] = {
                            "entries": self.eventsByCpuId[cpu_id][name]["entries"],
                            "exits": self.eventsByCpuId[cpu_id][name]["exits"],
                            "spans": self.eventsByCpuId[cpu_id][name]["spans"],
                            "callstack_user": self.eventsByCpuId[cpu_id][name]["callstack_user"],
                            "mean": 0,
                            "stdev": 0,
                        }


        for name in eventsByName:
            try:
                eventsByName[name]["mean"] = statistics.mean(eventsByName[name]["spans"])
                eventsByName[name]["stdev"] = statistics.stdev(eventsByName[name]["spans"])
            except:
                eventsByName[name]["mean"] = float(eventsByName[name]["spans"][0])
                eventsByName[name]["stdev"] = 0.0


        return eventsByName

    def average_durations(self):
        durations = {}
        flattened_event_list = self.flatten()
        
        for name in flattened_event_list:
            average = sum(flattened_event_list[name]["spans"]) / len(flattened_event_list[name]["spans"])
            durations[name] = average

        return durations








######################################################################################

def read_from_trace():
    global pid
    print("reading from trace file...")
    # Iterate the trace messages.
    for idx, msg in enumerate(msg_it):
        if idx == 100000000000000:
            break
        # `bt2._EventMessageConst` is the Python type of an event message.
        if type(msg) is bt2._EventMessageConst:

            if msg.event["pid"] not in [48075, 48283, 48473, 48663]:
                continue

            cs_user = [hex(x)[2:] for x in msg.event["callstack_user"]]


            event = {
                "cpu_id": msg.event["cpu_id"],
                "name": msg.event.name,
                "timestamp": msg.default_clock_snapshot.ns_from_origin,
                "callstack_user": cs_user
            }
            event_list.add(event)





def create_pair_list_from_trace():

    read_from_trace()

    print("Writing the pair list...")



    pairlist = []

    f = open("pairlist.csv", "w")
    f.write("Id,Source,Target,Interval\n")

    count = -1
    for i in range(event_list.no_of_ele()):
        keys = [zz for zz in event_list.eventsByCpuId[i]]
        for j in range(len(keys)):

            syscall = keys[j]
            length = 0
            if len(event_list.eventsByCpuId[i][syscall]['spans']) <= len(event_list.eventsByCpuId[i][syscall]['callstack_user']):
                length = len(event_list.eventsByCpuId[i][syscall]['spans'])
            else:
                length = len(event_list.eventsByCpuId[i][syscall]['callstack_user'])

            for k in range(length):
                period = event_list.eventsByCpuId[i][syscall]['spans'][k]
                callstack = event_list.eventsByCpuId[i][syscall]['callstack_user'][k]
                if len(callstack) > 1:
                    callstack.reverse()
                    for l in range(len(callstack)-1):
                        count = count+1
                        str_opt = str(count)+","+callstack[l]+","+callstack[l+1]+","+str(period)+"\n"
                        f.write(str_opt)
                        pairlist.append(str_opt)




    f.close()

    print("pair list created. Now import it to gephi.")




#########################################################################################





############################################################################################################

try:
    print("format: [mode] [procname filter] [pid filter] [perf file] [trace folder] [threshold in micro seconds] [gephi export file - optional (to be used with mode 2)]"+
        "\nModes:- \n0: Regular statistical debugging\n1: function pair list generation\n2: context aware statistical debugging")

    if len(sys.argv) < 6:
        print("Some arguments are missing.")
        sys.exit()
    elif int(sys.argv[1]) > 2 or int(sys.argv[1]) < 0:
        print("Invalid arguments.")
        sys.exit()
except:
    print("\n\nCorrect format: [mode] [procname filter] [pid filter] [perf file] [trace folder] [threshold in micro seconds] [gephi export file - optional (to be used with mode 2)]"+
        "\nModes:- \n0: Regular statistical debugging\n1: function pair list generation\n2: context aware statistical debugging")
    sys.exit()




mode = int(sys.argv[1])

procname = sys.argv[2]

pid = int(sys.argv[3])

perf_file = sys.argv[4]

trace_folder = sys.argv[5]

threshold = int(sys.argv[6])


gephi_file = ""

if mode == 2:
    gephi_file = sys.argv[7]




# Create a map of syscalls
syscalls = [] 

# Create a trace collection message iterator with this path.
msg_it = bt2.TraceCollectionMessageIterator(trace_folder)

# Last event's time (ns from origin).
last_event_ns_from_origin = None

event_list = EventList(perf_file, procname, threshold)




if mode == 0:
    print("Regular statistical debugging selected.")
    print("Starting...")
    read_from_trace()
    event_list.final_non_weighted_calculations()
    print("Complete!")
elif mode == 1:
    print("Generate function pair list selected.")
    print("Starting...")
    create_pair_list_from_trace()
    print("Complete! Next use the file to input into gephi and then export from gephi and use mode 2 for context aware statistical debugging.")
elif mode == 2:
    print("Generate context aware statistical debugging selected.")
    print("Starting...")
    read_from_trace()
    event_list.final_weighted_calculations()
    print("Complete!")






# # event_list.print_all()

# event_list_flattened = event_list.flatten()

# df_event_list_flattened = pd.DataFrame.from_records(event_list_flattened)
# print(df_event_list_flattened)

 


# averages = event_list.average_durations()
# df_event_list_averages = pd.DataFrame.from_records(averages, index=['1'])
# print(df_event_list_averages)


# import matplotlib.pyplot as plt

# fig = plt.figure()
# ax = fig.add_axes([0,0,1,1])
# ax.set_title('Average durations of system calls')
# events = averages.keys()
# durations = averages.values()
# ax.bar(events,durations)
# plt.xlabel('System Calls')
# plt.xticks(rotation = 45)
# plt.ylabel('Duration (ns)')
# plt.yticks(rotation=45)
# plt.show()

