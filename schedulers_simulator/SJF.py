from Process import Process
from gantt_chart import redraw_gantt
import matplotlib.pyplot as plt
import time
import copy 
import bisect
from queue import Queue

def push_arrived_process(processes: list[Process], ready_queue: list[Process]):
    i = 0 
    while i < len(processes):
        if(processes[i].arrival_time == 0):
            bisect.insort(ready_queue, processes[i], key=lambda x: (x.burst_time, x.num))
            processes.pop(i)
            continue
        i+=1

def proceed_time(processes: list[Process]):
    for process in processes:
        process.arrival_time -= 1

def sjf_preemptive(processes: list[Process], new_process_queue = None, live_sim: bool = False, pause_event = None, fig = None, ax = None)->tuple[list, int, float, float]:
    time_counter = 0
    ready_queue = []
    history = []
    processes = copy.deepcopy(processes)   
    number_of_processes = len(processes)

    # Sorting the processes according to their arrival time 
    processes = sorted(processes, key=lambda x: (x.arrival_time, x.num))

    turn_around_time = 0
    average_waiting_time = 0

    # Scheduler 
    while (ready_queue or processes):
        # Checking for pause
        if(live_sim):
            if pause_event:
                pause_event.wait() 

            if new_process_queue:
                while not new_process_queue.empty():
                    new_p = new_process_queue.get()
                    new_p.original_arrival_time = new_p.arrival_time + time_counter 
                    processes.append(new_p)
                    number_of_processes += 1 
                    print(f"\n [+] P{new_p.num} joined the simulation!")

        # Checking for arrived processes
        push_arrived_process(processes, ready_queue)

        # Skip idle cases
        if not ready_queue:
            time_counter += 1
            proceed_time(processes)
            if live_sim:
                time.sleep(1) 
            continue

        # Running a process for 1 sec
        running_process = ready_queue[0]
        running_process.burst_time -= 1
        time_counter += 1

        # Recording for the Gantt Chart
        if history and history[-1][0] == running_process.num:
            history[-1] = (history[-1][0], history[-1][1], time_counter)
        else:
            history.append((running_process.num, time_counter - 1, time_counter))

        if live_sim:
            print(f"\n{'─' * 40}")
            print(f"  ⏱  Time : {time_counter}")
            print(f"{'─' * 40}")
            
            # Running process
            print(f"  ▶  Running  : P{ready_queue[0].num}  (remaining: {ready_queue[0].burst_time})")
            
            # Queue
            queue_str = "  →  ".join(f"P{p.num}({p.burst_time})" for p in ready_queue[1:])
            print(f"  ⏳ Waiting  : {queue_str if queue_str else 'empty'}")

            time.sleep(1)
            
            redraw_gantt(ax, history)
            fig.canvas.draw()                     # type: ignore
            fig.canvas.flush_events()             # type: ignore

        # Process termination
        if running_process.burst_time == 0:
            turn_around_time     += time_counter - running_process.original_arrival_time
            average_waiting_time += time_counter - running_process.original_arrival_time - running_process.original_burst_time
            print(f"\n  ✔  P{running_process.num} finished at t={time_counter}")
            print(f"{'─' * 40}")
            ready_queue.pop(0)

        # Moving time by one second
        proceed_time(processes)

    
    if number_of_processes > 0:
        turn_around_time     = float(turn_around_time/number_of_processes)
        average_waiting_time = float(average_waiting_time/number_of_processes)
    else:
        turn_around_time = 0.0
        average_waiting_time = 0.0

    return (history, time_counter, turn_around_time, average_waiting_time)