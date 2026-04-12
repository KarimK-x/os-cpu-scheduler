# Inputs :
# Type of scheduler + no of Processes ready to run currently + required information about each process according to the scheduler type.
# A new process can be added dynamically while the scheduler is running.

# Note : Don't ask the user for unused info
# Example: If the user chose FCFS scheduler no need to ask him what is the priority numbers.

# Operation:
# • A live scheduler is run with each 1 unit of time mapped to 1 second
# • Remaining burst time table is updated as time progresses.
# • An option to run the currently existing processes only without live scheduling must be available.
# • Your project must be built, and you must generate a ready to run executable file
# • You must deliver a GUI desktop application.

# Outputs:
# • Timeline showing the order and time taken by each process (Gantt Chart) drawn live.
# • Average waiting time and average turnaround time
# • Remaining burst time updated table live

from Process import Process

def push_arrived_process(processes: list[Process], ready_queue: list[Process]):
    i = 0 
    while i < len(processes):
        if(processes[i].arrival_time == 0):
            ready_queue.append(processes[i])
            processes.pop(i)
            continue
        i+=1

def proceed_time(processes: list[Process]):
    for process in processes:
        process.arrival_time -= 1

def sjf_preemptive(processes: list[Process])->list[list[(int, int, int), int, int, int]]:
    time_counter = 0
    processes = []
    ready_queue = []
    history = []
    number_of_processes = len(processes)

    # Sorting the processes according to their arrival time 
    processes = sorted(processes, key=lambda x: (x.arrival_time, x.num))

    # Putting proccesses in the ready queue
    # push_arrived_process(processes, ready_queue)

    # for process in processes:
    #     print(f"P{process.num} | arrival time = {process.arrival_time} | burst time = {process.burst_time}")

    turn_around_time = 0
    average_waiting_time = 0

    # Scheduler 
    while (ready_queue or processes):
        # Checking for arrived processes
        push_arrived_process(processes, ready_queue)

        # Skip idle cases
        if not ready_queue:
            time_counter += 1
            proceed_time(processes)
            continue

        # Sorting the ready_queue according least remaining burst time
        ready_queue = sorted(ready_queue, key=lambda x: (x.burst_time, x.num))

        # Running a process for 1 sec
        running_process = ready_queue[0]
        running_process.burst_time -= 1
        time_counter += 1

        # Recording for the Gantt Chart
        if history and history[-1][0] == running_process.num:
            history[-1] = (history[-1][0], history[-1][1], time_counter)
        else:
            history.append((running_process.num, time_counter - 1, time_counter))

        # Computing waiting time for every process
        i = 1
        while i < len(ready_queue):
            ready_queue[i].waiting_time += 1
            i+=1

        # Process termination and computing turnaround time and average waiting time
        if(running_process.burst_time == 0):
            turn_around_time += time_counter - running_process.original_arrival_time
            average_waiting_time += running_process.waiting_time
            print(f"P{running_process.num} finished at {time_counter}")
            ready_queue.pop(0)

        # Moving time by one second
        proceed_time(processes)

    turn_around_time = float(turn_around_time/number_of_processes)
    average_waiting_time = float(average_waiting_time/number_of_processes)
    print(f"Turnaround time = {turn_around_time}")
    print(f"Average Waiting time = {average_waiting_time}")
    return [history, time_counter, turn_around_time, average_waiting_time]