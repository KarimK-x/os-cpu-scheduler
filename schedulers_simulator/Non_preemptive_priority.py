
from Process import Process
from gantt_chart import redraw_gantt
import time
import copy 

# Algorithm operation
def Non_preemptive_priority(processes: list[Process], new_process_queue = None,live_sim: bool = False,pause_event = None, fig = None, ax = None, on_progress = None):
    
    # Add processes into job queue
    job_queue       = copy.deepcopy(processes)
    number_of_processes = len(job_queue)
    ready_queue     = []
    gantt           = []
    current_time    = 0
    average_turnaround_time = 0
    average_waiting_time    = 0
    total_waiting_time = 0
    total_turnaround = 0
    
    
    while(len(job_queue) != 0 or len(ready_queue) != 0):   # check that all process are transfered to ready queue and executed
        
        # Checking for pause
        if(live_sim):
            if pause_event:
                pause_event.wait() 

            if new_process_queue:
                while not new_process_queue.empty():
                    new_p = new_process_queue.get()
                    new_p.original_arrival_time = new_p.arrival_time + current_time 
                    processes.append(new_p)
                    number_of_processes += 1 
                    print(f"\n [+] P{new_p.num} joined the simulation!")
                    
                    # Add new extra process in the job queue
                    job_queue.append(new_p)
                    
        # Put processes in the ready queue
        for process in job_queue.copy():
            if(current_time >= process.arrival_time):
                ready_queue.append(process)
                job_queue.remove(process)
                
        # Handle if the ready queue is empty by incrementing current_time by 1 second
        if(len(ready_queue) == 0):
            current_time += 1
            if live_sim:
                time.sleep(1)
                if on_progress is not None:
                    on_progress(gantt, current_time)
            continue
        
        # Determine priority of the process if there are 2 processes have the same priority use FCFS algorithm 
        ready_process = ready_queue[0]
        for process in ready_queue:
            if(process.priority < ready_process.priority or 
              (process.priority == ready_process.priority and
               process.arrival_time < ready_process.arrival_time)):
                ready_process = process   
                       
        # Execute process  
        ready_process.burst_time -=1
        start_time = current_time
        finish_time = current_time + ready_process.original_burst_time
        
        for t in range(start_time, finish_time):
            current_time = t + 1
            # Recording for the Gantt Chart
            if (gantt and gantt[-1][0] == ready_process.num):
                gantt[-1] = (gantt[-1][0], gantt[-1][1], current_time)
            else:
                gantt.append((ready_process.num, t, current_time))
                
        # Live simulation                      
            if live_sim:
                print(f"\n{'─' * 40}")
                print(f"  ⏱  Time : {current_time}")
                print(f"{'─' * 40}")

                # Running process
                print(f"  ▶  Running  : P{ready_process.num}  (burst: {ready_process.burst_time})")

                # Queue
                queue_str = "  →  ".join(f"P{p.num}({p.burst_time})" for p in ready_queue[1:])
                print(f"  ⏳ Waiting  : {queue_str if queue_str else 'empty'}")

                # NOW we sleep. If paused here, the menu prints cleanly underneath the text above.
                time.sleep(1)

                if fig is not None and ax is not None:
                    redraw_gantt(ax, gantt)
                    fig.canvas.draw()                     # type: ignore
                    fig.canvas.flush_events()             # type: ignore
                if on_progress is not None:
                    on_progress(gantt, current_time)
        
        # Average waiting and turnaround time calculations            
        total_turnaround += current_time - ready_process.original_arrival_time
        total_waiting_time += current_time - ready_process.original_arrival_time - ready_process.original_burst_time
        ready_queue.remove(ready_process)
           
            
    average_turnaround_time = total_turnaround / number_of_processes
    average_waiting_time = total_waiting_time /  number_of_processes 
    return(gantt,current_time,average_turnaround_time,average_waiting_time) 
                                          
            