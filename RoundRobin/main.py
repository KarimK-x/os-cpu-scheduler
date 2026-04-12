from round_robin import Process, RoundRobinScheduler

def main():
    # Replace by user input
    #======================
    num_of_processes = 3
    current_processes : list[Process] = []
    for i in range(num_of_processes):
        current_processes.append(Process(
            num= i,
            arrival_time= 0,
            burst_time= int(input(f"Enter Burst time for P{i}: "))
        ))
    print([(i.num, i.burst_time) for i in current_processes])
    quantum = 4
    #======================
    
    #Main Flow
    rrScheduler = RoundRobinScheduler(quantum)
    run_1 = rrScheduler.runRoundRobin(current_processes)
    rrScheduler.drawGant(run_1)
    print("Average waiting time is ", rrScheduler.calculateAverageWaitingTime(run_1))
    print("Average turnaround time is ", rrScheduler.calculateAverageTurnAroundTime(run_1))

if __name__ == "__main__":
    main()