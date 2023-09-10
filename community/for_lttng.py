import bt2
import sys
import pandas as pd
import re
import statistics
import math

class EventList:

    function_address = []
    function_name = []
    unique_functions = []
    func_set = set()
    gephi_headers = []

    def __init__(self):
        self.eventsByCpuId = {}

        perf_file = "/home/a/Desktop/c_code/bin/Debug/perf_output.txt"

        with open(perf_file) as file:

            for line in file:
                
                line = line.replace("\n","")
                line = line.strip()


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
        
        
        event_type = parts[0]

        if event_type != "syscall":
            return

        event_name = parts[2]
        event_is_entry = parts[1] == "entry"

        
        
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



        for j in range(len(event["callstack_user"])):
            for i in range(len(self.function_address)):
                if event["callstack_user"][j] == self.function_address[i]:
                    event["callstack_user"][j] = self.function_name[i]
                self.func_set.add(event["callstack_user"][j])
                




        if num_entries == num_exits and event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].append(event["timestamp"])
            self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].append(event["callstack_user"])
        elif num_entries > num_exits and not event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["exits"].append(event["timestamp"])
        elif num_entries > num_exits and event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].pop()
            self.eventsByCpuId[event["cpu_id"]][event_name]["entries"].append(event["timestamp"])
            self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].pop()
            self.eventsByCpuId[event["cpu_id"]][event_name]["callstack_user"].append(event["callstack_user"])
        elif event_is_entry:
            self.eventsByCpuId[event["cpu_id"]][event_name]["exits"].pop()


        num_exits = len(self.eventsByCpuId[event["cpu_id"]][event_name]["exits"])
        if num_entries != 0 and num_entries == num_exits:
            self.eventsByCpuId[event["cpu_id"]][event_name]["spans"].append(
                self.eventsByCpuId[event["cpu_id"]][event_name]["exits"][num_exits - 1] -
                self.eventsByCpuId[event["cpu_id"]][event_name]["entries"][num_entries - 1]
            )


    def final_weighted_calculations(self):
        functions = self.generate_functions_with_weights()

        threshold = 10

        for name in functions:
            for i in functions[name]["periods"]:
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
                except:
                    importance_p = 0.0


        for i in range(len(self.gephi_headers)):

            f = open(self.gephi_headers[i]+".csv", "w")
            f.write("Function,Total_Syscalls,Total_Syscalls_Success,Total_Syscalls_Failed,Min,Max,Average,Stdev,Failure,Context,Increase,Importance\n")

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

                string_builder = name+","+str(len(functions[name]["periods"]))+","+str(functions[name]["successes"])+","+str(functions[name]["fails"])+","+str(minimum)+","+str(maximum)+","+str(mean)+","+str(stdev)+","+str(functions[name]["failure"][i])+","+str(functions[name]["context"][i])+","+str(functions[name]["increase"][i])+","+str(functions[name]["importance"][i])+"\n"
                f.write(string_builder)

            f.close()

        print("Writing to file complete.")


    def generate_functions_with_weights(self):
        functions = self.generate_functions()

        gephi_file = "/home/a/Desktop/c_code/bin/Debug/gephi.csv"
        print("Reading gephi data...")
        with open("gephi.csv") as file:
            header_ignore = True
            for line in file:
                if header_ignore:
                    line = line.replace("\n","")
                    self.gephi_headers = line.split(",")[1:]
                    header_ignore = False
                    continue

                line = line.replace("\n","")

                func_data = float(line.split(","))

                for name in functions:
                    if name == func_data[0]:
                        functions[name]["weight"] += [float(p) for p in func_data[1:]]
                        break

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




def create_pair_list_from_trace():

    # Create a map of syscalls
    syscalls = [] 

    # Create a trace collection message iterator with this path.
    msg_it = bt2.TraceCollectionMessageIterator("test")

    # Last event's time (ns from origin).
    last_event_ns_from_origin = None

    event_list = EventList()

    # Iterate the trace messages.
    for idx, msg in enumerate(msg_it):
        if idx == 1000000000000:
            break
        # `bt2._EventMessageConst` is the Python type of an event message.
        if type(msg) is bt2._EventMessageConst:

            if msg.event["pid"] != 8715:
                continue

            cs_user = [hex(x)[2:] for x in msg.event["callstack_user"]]


            event = {
                "cpu_id": msg.event["cpu_id"],
                "name": msg.event.name,
                "timestamp": msg.default_clock_snapshot.ns_from_origin,
                "callstack_user": cs_user
            }
            event_list.add(event)




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





print(event_list.generate())


# event_list.print_all()

event_list_flattened = event_list.flatten()

df_event_list_flattened = pd.DataFrame.from_records(event_list_flattened)
print(df_event_list_flattened)

 


averages = event_list.average_durations()
df_event_list_averages = pd.DataFrame.from_records(averages, index=['1'])
print(df_event_list_averages)


import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.set_title('Average durations of system calls')
events = averages.keys()
durations = averages.values()
ax.bar(events,durations)
plt.xlabel('System Calls')
plt.xticks(rotation = 45)
plt.ylabel('Duration (ns)')
plt.yticks(rotation=45)
plt.show()

