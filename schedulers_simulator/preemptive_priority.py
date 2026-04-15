import heapq
from Process import Process
from gantt_chart import redraw_gantt
import matplotlib.pyplot as plt
import time
import copy



def preemptive_priority_scheduler(process_list: list[Process], new_process_queue = None,live_sim: bool = False,pause_event = None, fig = None, ax = None)->tuple[list, int, float, float]:
    process_list = copy.deepcopy(process_list)

    #sort by arrival time, priority in case of same arrival time
    #last element=first to be executed
    process_list.sort(key=lambda x:(x.arrival_time,x.priority,x.num),reverse=True) 
    current_time=0
    ready_queue=[] 
    no=len(process_list)
    total_waiting_time = 0
    total_turnaround_time = 0
    history=[]


    #for tracking
    prev_process=None
    start_time=0

    while process_list or ready_queue:

        #dynamic-adding
        if live_sim:
            if pause_event:
                pause_event.wait()
            
            if new_process_queue:
                added_new = False
                while not new_process_queue.empty():
                    new_p = new_process_queue.get()
                    new_p.arrival_time = current_time + new_p.arrival_time
                    process_list.append(new_p)
                    no += 1  # Update total count for averages
                    added_new = True
                    print(f"\n [+] P{new_p.num} joined the simulation!")
                
                # If we added processes, we MUST re-sort the list so they pop in the correct order!
                if added_new:
                    process_list.sort(key=lambda x:(x.arrival_time,x.priority,x.num),reverse=True)


        while process_list and process_list[-1].arrival_time<=current_time:
            available_process=process_list.pop()
            #push to minimum heap, ordered based on priority then arrival time then id
            heapq.heappush(ready_queue,available_process)
            
        #idle time, no available processes yet    
        if not ready_queue:
            if prev_process is not None:
                print(f"Time {start_time:2d} -> {current_time:2d} : Process {prev_process.num} (Completed)")
                prev_process = None
            current_time+=1

            if history and history[-1][0] == "Idle":
                # If we were already idle, stretch the idle block
                history[-1] = ("Idle", history[-1][1], current_time)
            else:
                # If we just became idle, create a new idle block
                history.append(("Idle", current_time - 1, current_time))
            if live_sim:
                time.sleep(1)
                redraw_gantt(ax, history)
                fig.canvas.draw()
                fig.canvas.flush_events()

            continue

        current_process=heapq.heappop(ready_queue)

        #check for switching
        if prev_process != current_process:
            if prev_process is not None:
                #print previous process in case of switching
                state = "Completed" if prev_process.burst_time == 0 else f"Preempted, Remaining time: {prev_process.burst_time}"
                print(f"Time {start_time:2d} -> {current_time:2d} : Process {prev_process.num} ({state})")
            
            #start new process
            start_time=current_time
            prev_process=current_process

        #execute for 1 time unit
        current_process.burst_time-=1
        current_time+=1

        #Record for the Gantt Chart
        if history and history[-1][0] == current_process.num:
            # If it's the same process, just stretch the end time
            history[-1] = (history[-1][0], history[-1][1], current_time)
        else:
            # If it's a new process, create a new block
            history.append((current_process.num, current_time - 1, current_time))

        if live_sim:
            time.sleep(1)
            redraw_gantt(ax, history)
            fig.canvas.draw()
            fig.canvas.flush_events()            


        if(current_process.burst_time>0):
            heapq.heappush(ready_queue,current_process)
        else:
            current_process.turn_around_time = current_time - current_process.arrival_time
            current_process.waiting_time = current_process.turn_around_time - current_process.original_burst_time
            current_process.finish_time=current_time
            total_turnaround_time+=current_process.turn_around_time 
            total_waiting_time+=current_process.waiting_time

    if prev_process is not None:
        state = "Completed" if prev_process.burst_time == 0 else f"Preempted, Remaining time: {prev_process.burst_time}"
        print(f"Time {start_time:2d} -> {current_time:2d} : Process {prev_process.num} ({state})")
    average_turnaround_time=float(total_turnaround_time/no)
    average_waiting_time=float(total_waiting_time/no)
    return (history, current_time,average_turnaround_time, average_waiting_time)













        
