import pandas as pd
import os

try: 
    os.mkdir("stats")
except OSError as error: 
    print(error)


def analyze_block_rq():
    print("Blockrq Start")
    df = pd.read_csv('block_rq.csv', na_filter=True)
    df.dropna(inplace = True)

    Getrq_Insert_Threshold = df.iloc[:,0].mean() + df.iloc[:,0].std()
    Insert_Issue_Threshold = df.iloc[:,1].mean() + df.iloc[:,1].std()
    Issue_Complete_hreshold = df.iloc[:,2].mean() + df.iloc[:,2].std()


    unique_functions_in_callstacks = []


    for i in range(len(df.index)):
        Getrq_Callstack = df.iloc[i:i+1,3].values[0].split(' ')
        for j in Getrq_Callstack:
            if j not in unique_functions_in_callstacks:
                unique_functions_in_callstacks.append(j)


    Getrq_Insert_Success = [0] * len(unique_functions_in_callstacks)
    Getrq_Insert_Fail = [0] * len(unique_functions_in_callstacks)
    Insert_Issue_Success = [0] * len(unique_functions_in_callstacks)
    Insert_Issue_Fail = [0] * len(unique_functions_in_callstacks)
    Issue_Complete_Success = [0] * len(unique_functions_in_callstacks)
    Issue_Complete_Fail = [0] * len(unique_functions_in_callstacks)

    for i in range(len(unique_functions_in_callstacks)):
        for j in range(len(df.index)):
            Getrq_Callstack = df.iloc[j:j+1,3].values[0]
            if unique_functions_in_callstacks[i] not in Getrq_Callstack:
                continue
            else:
                if df.iloc[j:j+1,0].values[0] < Getrq_Insert_Threshold:
                    Getrq_Insert_Success[i] = Getrq_Insert_Success[i] + 1
                else:
                    Getrq_Insert_Fail[i] = Getrq_Insert_Fail[i] + 1

                if df.iloc[j:j+1,1].values[0] < Insert_Issue_Threshold:
                    Insert_Issue_Success[i] = Insert_Issue_Success[i] + 1
                else:
                    Insert_Issue_Fail[i] = Insert_Issue_Fail[i] + 1

                if df.iloc[j:j+1,2].values[0] > Issue_Complete_hreshold:
                    Issue_Complete_Success[i] = Issue_Complete_Success[i] + 1
                else:
                    Issue_Complete_Fail[i] = Issue_Complete_Fail[i] + 1

    f = open("stats\\"+"function_stats_block_rq.csv", "w")
    f.write("Function,Getrq_Insert_Success,Getrq_Insert_Fail,Insert_Issue_Success,Insert_Issue_Fail,Issue_Complete_Success,Issue_Complete_Fail\n")


    for i in range(len(unique_functions_in_callstacks)):
        f.write(unique_functions_in_callstacks[i]+","+str(Getrq_Insert_Success[i])+","+str(Getrq_Insert_Fail[i])+","+str(Insert_Issue_Success[i])+","+str(Insert_Issue_Fail[i])+","+str(Issue_Complete_Success[i])+","+str(Issue_Complete_Fail[i])+"\n")


    f.close()

    print("Blockrq Done")



def analyze_sched():

    print("Sched Start")

    df = pd.read_csv('sched.csv', na_filter=True)
    df.dropna(inplace = True)

    #this needs fixing, for some reason .std is returning nan
    Waking_Switch_Threshold = df.iloc[:,0].mean() + df.iloc[:,0].std()

    

    unique_functions_in_callstacks = []

    for i in range(len(df.index)):
        Waking_Callstack = df.iloc[i:i+1,1].values[0].split(' ')
        Switch_Callstack = df.iloc[i:i+1,2].values[0].split(' ')
        Callstack = Waking_Callstack + Switch_Callstack
        for j in Callstack:
            if j not in unique_functions_in_callstacks:
                unique_functions_in_callstacks.append(j)
    
    Waking_Switch_Success = [0] * len(unique_functions_in_callstacks)
    Waking_Switch_Fail = [0] * len(unique_functions_in_callstacks)

    for i in range(len(unique_functions_in_callstacks)):
        for j in range(len(df.index)):
            Waking_Callstack = df.iloc[j:j+1,1].values[0].split(' ')
            Switch_Callstack = df.iloc[j:j+1,2].values[0].split(' ')
            Callstack = Waking_Callstack + Switch_Callstack
            if unique_functions_in_callstacks[i] not in Callstack:
                continue
            else:
                if df.iloc[j:j+1,0].values[0] < Waking_Switch_Threshold:
                    Waking_Switch_Success[i] = Waking_Switch_Success[i] + 1
                else:
                    Waking_Switch_Fail[i] = Waking_Switch_Fail[i] + 1

    f = open("stats\\"+"function_stats_sched.csv", "w")
    f.write("Function,Waking_Switch_Success,Waking_Switch_Fail\n")

    for i in range(len(unique_functions_in_callstacks)):
        f.write(unique_functions_in_callstacks[i]+","+str(Waking_Switch_Success[i])+","+str(Waking_Switch_Fail[i])+"\n")


    f.close()

    print("Sched Done")



def analyze_all():
    analyze_block_rq()
    analyze_sched()



print("Start")
analyze_all()
print("End")
