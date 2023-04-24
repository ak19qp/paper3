from statistics import stdev


class Node:
  
    # Function to initialise the node object
    def __init__(self, data):
        self.data = data  # Assign data
        self.next = None  # Initialize next as null
        self.time_counter = []
        self.last_count = -1
  
  
# Linked List class contains a Node object
class LinkedList:
  
    # Function to initialize head
    def __init__(self):
        self.head = None
  
    # This function prints contents of linked list
    # starting from head
    def printList(self):
        temp = self.head
        while (temp):
            print(temp.data)
            temp = temp.next

    def getLast(self):
        temp = self.head
        lasttemp = None
        while (temp):
            lasttemp = temp
            temp = temp.next
        return lasttemp

    def getData(self):
        temp = self.head
        return temp.data

    def searchValue(self, val):
        temp = self.head
        while (temp):
            if temp.data == val:
                return True
            temp = temp.next
        return False






ignore_kernel_parents = False
samples = 100
rank_cut_off_number = 2000 #num of methods to follow
array=[]
last_parrent_index = 0
current_count = -1

connections = {}

ignore_next_child = False


kernel_exclusion_string = "[k]"
if ignore_kernel_parents:
    kernel_exclusion_string = ""

                    
for count in range(samples):

    print("\nProgress: " + str(int(100*count/samples)) + "%  |  Loop: " + str(count) + "/" + str(samples) + "\n")
    
    with open('perf'+str(count)+'.txt') as f:
        while True:

            line = f.readline().strip()
            if not line:
                break
            
            

            if line != None and line != "":


                if line.count('%') > 1 and kernel_exclusion_string not in line:

                    ignore_next_child = False
                    #if "libxul.so" in line or "libc-2.31.so " in line:
                    parent = line.split("] ")[-1]

                    #check if parent already exist
                    found = False
                    counter = -1
                    for k in array:
                        counter = counter + 1
                        if k.getData() == parent:
                            found = True
                            
                            if k.head.last_count <= count-2:
                                k.head.time_counter.append(1)
                            else:
                                if k.head.last_count != count:
                                    k.head.time_counter[-1] = k.head.time_counter[-1] + 1

                            k.head.last_count = count
                            last_parrent_index = counter
                            break
                    if not found:
                        llist = LinkedList()
                        llist.head = Node(parent)
                        llist.head.last_count = count
                        llist.head.time_counter.append(1)
                       
                        array.append(llist)
                        last_parrent_index = len(array) - 1


                elif kernel_exclusion_string in line:
                    ignore_next_child = True

                else:
                    if ignore_next_child:

                        ignore_next_child = False

                    elif len(array) > 0:
                        children = line.split("% ",1)[1].split(";")
                        parent = array[last_parrent_index].getData()

                        for i in children:
                            connection = parent + "-----" + i
                            if connection in connections:
                                connections[connection] += 1
                            else:
                                connections[connection] = 1

                            parent = i


                            found = False
                            counter = -1
                            for k in array:
                                counter = counter + 1
                                if k.getData() == i:
                                    found = True
                                    
                                    if k.head.last_count <= count-2:
                                        k.head.time_counter.append(1)
                                    else:
                                        if k.head.last_count != count:
                                            k.head.time_counter[-1] = k.head.time_counter[-1] + 1

                                    k.head.last_count = count
                                    last_parrent_index = counter
                                    break
                            if not found:
                                llist = LinkedList()
                                llist.head = Node(i)
                                llist.head.last_count = count
                                llist.head.time_counter.append(1)
                               
                                array.append(llist)
                                last_parrent_index = len(array) - 1



                   

        
           


connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)


sortedarray = []

sortedarrayfinal = []


sortedarrayheadding = []
sortedarraydata = []


if len(array) < rank_cut_off_number:
    rank_cut_off_number = len(array)

#sorting in desc by number of time_counter datasets
while len(array)>0:
    length = 0
    biggest_index = 0
    c = -1
    for k in array:
        c = c + 1
        if length < len(k.head.time_counter):
            length = len(k.head.time_counter)
            biggest_index = c
    
    tempstore = array.pop(biggest_index)
    sortedarray.append(tempstore)

    if len(sortedarray) == rank_cut_off_number:
        break
    



#Next sorting based on standard deviation
while len(sortedarray)>0:
    sd = 0
    biggest_index = 0
    c = -1
    for k in sortedarray:
        c = c + 1
        if len(k.head.time_counter) > 1 and sd < stdev(k.head.time_counter):
            sd = stdev(k.head.time_counter)
            biggest_index = c
    
    tempstore = sortedarray.pop(biggest_index)
    sortedarrayfinal.append(tempstore)
    sortedarrayheadding.append(tempstore.head.data)
    sortedarraydata.append(tempstore.head.time_counter)




f = open("output1.txt", "w")

for k in range(len(sortedarraydata)):

    print(str(sortedarraydata[k]))

    f.write(str(sortedarraydata[k])+"\n")

    print(sortedarrayheadding[k])

    f.write(sortedarrayheadding[k]+"\n")

    f.write("\n")
    print("\n")

f.close()

print("Output1 generated!")






f = open("output2.txt", "w")
for item in connections:
    if item[0].split("-----")[1] in sortedarrayheadding:
        f.write(str(item)+"\n")
        print(item) # gives a tuple

f.close()

print("Output2 generated!")



f = open("output3.csv", "w")
stringbuilder = ""
for k in sortedarrayheadding:
    stringbuilder = stringbuilder + '"' + k + '",'
stringbuilder = stringbuilder + "\n"



alldone = False

while not alldone:
    alldone = True
    for i in range(len(sortedarraydata)):
        if len(sortedarraydata[i]) > 0:
            tempdata = str(sortedarraydata[i].pop(0))
            stringbuilder = stringbuilder + tempdata + ","
        else:
            stringbuilder = stringbuilder + ","

        if len(sortedarraydata[i]) > 0:
            alldone = False

    stringbuilder = stringbuilder + "\n"

f.write(stringbuilder)
f.close()

print("Output3 generated!")

print("All complete!")