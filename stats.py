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


    unique_function_paths_in_callstacks = []


    for i in range(len(df.index)):
        Getrq_Callstack = df.iloc[i:i+1,3].values[0]
        if Getrq_Callstack not in unique_function_paths_in_callstacks:
            unique_function_paths_in_callstacks.append(Getrq_Callstack)




    Getrq_Insert_Success = [0] * len(unique_function_paths_in_callstacks)
    Getrq_Insert_Fail = [0] * len(unique_function_paths_in_callstacks)
    Insert_Issue_Success = [0] * len(unique_function_paths_in_callstacks)
    Insert_Issue_Fail = [0] * len(unique_function_paths_in_callstacks)
    Issue_Complete_Success = [0] * len(unique_function_paths_in_callstacks)
    Issue_Complete_Fail = [0] * len(unique_function_paths_in_callstacks)

    for i in range(len(unique_function_paths_in_callstacks)):
        for j in range(len(df.index)):
            Getrq_Callstack = df.iloc[j:j+1,3].values[0]
            if unique_function_paths_in_callstacks[i] not in Getrq_Callstack:
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

    f = open("function_stats_block_rq.csv", "w")
    f.write("Function,Getrq_to_Insert_Success,Getrq_to_Insert_Fail,Getrq_to_Insert_Failure,Getrq_to_Insert_Context,Getrq_to_Insert_Increase,Insert_to_Issue_Success,Insert_to_Issue_Fail,Insert_to_Issue_Failure,Insert_to_Issue_Context,Insert_to_Issue_Increase,Issue_to_Complete_Success,Issue_to_Complete_Fail,Issue_to_Complete_Failure,Issue_to_Complete_Context,Issue_to_Complete_Increase\n")



    for i in range(len(unique_function_paths_in_callstacks)):
        Getrq_to_Insert_Failure = Getrq_Insert_Fail[i] / (Getrq_Insert_Success[i] + Getrq_Insert_Fail[i])
        Getrq_to_Insert_Context = sum(Getrq_Insert_Fail) / sum(Getrq_Insert_Success) + sum(Getrq_Insert_Fail)
        Getrq_to_Insert_Increase = Getrq_to_Insert_Failure - Getrq_to_Insert_Context
        
        Insert_to_Issue_Failure = Insert_Issue_Fail[i] / (Insert_Issue_Success[i] + Insert_Issue_Fail[i])
        Insert_to_Issue_Context = sum(Insert_Issue_Fail) / sum(Insert_Issue_Success) + sum(Insert_Issue_Fail)
        Insert_to_Issue_Increase = Insert_to_Issue_Failure - Insert_to_Issue_Context

        Issue_to_Complete_Failure = Issue_Complete_Fail[i] / (Issue_Complete_Success[i] + Issue_Complete_Fail[i])
        Issue_to_Complete_Context = sum(Issue_Complete_Fail) / sum(Issue_Complete_Success) + sum(Issue_Complete_Fail)
        Issue_to_Complete_Increase = Issue_to_Complete_Failure - Issue_to_Complete_Context

        string = unique_function_paths_in_callstacks[i]+","+str(Getrq_Insert_Success[i])+","+str(Getrq_Insert_Fail[i])+","
        string = string + str(Getrq_to_Insert_Failure)+","+str(Getrq_to_Insert_Context)+","+str(Getrq_to_Insert_Increase)+","
        string = string + str(Insert_Issue_Success[i])+","+str(Insert_Issue_Fail[i])+","
        string = string + str(Insert_to_Issue_Failure)+","+str(Insert_to_Issue_Context)+","+str(Insert_to_Issue_Increase)+","
        string = string + str(Issue_Complete_Success[i])+"," +str(Issue_Complete_Fail[i])+","
        string = string + str(Issue_to_Complete_Failure)+","+str(Issue_to_Complete_Context)+","+str(Issue_to_Complete_Increase)+"\n"

        f.write(string)


    f.close()

    print("Blockrq Done")



def analyze_sched():

    print("Sched Start")

    df = pd.read_csv('sched.csv', na_filter=True)
    df.dropna(inplace = True)

    Waking_Switch_Threshold = df.iloc[:,0].mean() + df.iloc[:,0].std()

    unique_function_paths_in_callstacks = []

    for i in range(len(df.index)):
        Waking_Callstack = df.iloc[i:i+1,1].values[0]
        Switch_Callstack = df.iloc[i:i+1,2].values[0]
        Callstack = Waking_Callstack + Switch_Callstack
        if Callstack not in unique_function_paths_in_callstacks:
            unique_function_paths_in_callstacks.append(Callstack)
    
    Waking_Switch_Success = [0] * len(unique_function_paths_in_callstacks)
    Waking_Switch_Fail = [0] * len(unique_function_paths_in_callstacks)

    for i in range(len(unique_function_paths_in_callstacks)):
        for j in range(len(df.index)):
            Waking_Callstack = df.iloc[j:j+1,1].values[0]
            Switch_Callstack = df.iloc[j:j+1,2].values[0]
            Callstack = Waking_Callstack + Switch_Callstack
            if unique_function_paths_in_callstacks[i] not in Callstack:
                continue
            else:
                if df.iloc[j:j+1,0].values[0] < Waking_Switch_Threshold:
                    Waking_Switch_Success[i] = Waking_Switch_Success[i] + 1
                else:
                    Waking_Switch_Fail[i] = Waking_Switch_Fail[i] + 1

    f = open("function_stats_sched.csv", "w")
    f.write("Function,Waking_Switch_Success,Waking_Switch_Fail,Waking_Switch_Failure,Waking_Switch_Context,Waking_Switch_Increase\n")

    for i in range(len(unique_function_paths_in_callstacks)):

        Waking_Switch_Failure = Waking_Switch_Fail[i] / (Waking_Switch_Success[i] + Waking_Switch_Fail[i])
        Waking_Switch_Context = sum(Waking_Switch_Fail) / sum(Waking_Switch_Success) + sum(Waking_Switch_Fail)
        Waking_Switch_Increase = Waking_Switch_Failure - Waking_Switch_Context

        f.write(unique_function_paths_in_callstacks[i]+","+str(Waking_Switch_Success[i])+","+str(Waking_Switch_Fail[i])+","+str(Waking_Switch_Failure)+","+str(Waking_Switch_Context)+","+str(Waking_Switch_Increase)+"\n")

    f.close()

    print("Sched Done")



def analyze_all():
    analyze_block_rq()
    analyze_sched()



print("Start")
analyze_all()
print("End")
