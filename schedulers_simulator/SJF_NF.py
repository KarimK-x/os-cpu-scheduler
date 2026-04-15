from Process import Process
from gantt_chart import redraw_gantt
import matplotlib.pyplot as plt
import time

# Inputs :
# Type of scheduler + no of Processes ready to run currently + required information about each process according to the scheduler type.
# A new process can be added dynamically while the scheduler is running.

# Note : Don't ask the user for unused info
# Example: If the user chose FCFS scheduler no need to ask him what is the priority numbers.

# Operation:
# • A live scheduler is run with each 1 unit of time mapped to 1 second
# • Remaining burst timetable is updated as time progresses.
# • An option to run the currently existing processes only without live scheduling must be available.
# • Your project must be built, and you must generate a ready to run executable file
# • You must deliver a GUI desktop application.

# Outputs:
# • Timeline showing the order and time taken by each process (Gantt Chart) drawn live.
# • Average waiting time and average turnaround time
# • Remaining burst time updated table live

def sjf(processes: list[Process], live_sim: bool = False, fig = None, ax = None)->tuple[list, int, float, float]:

    readyqueue = []
    history = []
    processes_num = len(processes)
    processes_curr = processes_num
    turnaround_time = 0
    waiting_time = 0

    t = 0
    processes = sorted(processes, key=lambda x: (x.arrival_time, x.num))

    while readyqueue or processes_curr:
        for p in processes:
            if p.arrival_time <= t and p.isFinished==False:
                readyqueue.append(p)
                p.isFinished = True
                processes_curr-=1

        if not readyqueue:
            t+=1
            if live_sim:
                time.sleep(1)
            continue

        readyqueue = sorted(readyqueue, key=lambda x: (x.burst_time,x.num))

        burst = readyqueue[0].burst_time
        readyqueue[0].start_time = t
        readyqueue[0].finish_time = t + burst
        history.append([readyqueue[0].num, readyqueue[0].start_time, readyqueue[0].start_time+1])

        print(f"\n  ✔  P{readyqueue[0].num} started at t={t}")
        print(f"{'─' * 40}")

        if live_sim:
            j = 1
            while j<burst:
                time.sleep(1)
                redraw_gantt(ax, history)
                fig.canvas.draw()
                fig.canvas.flush_events()
                j+=1
                history[-1][2]+=1

        print(f"\n  ✔  P{readyqueue[0].num} finished at t={t+burst}")
        print(f"{'─' * 40}")


        turnaround_time += (readyqueue[0].finish_time - readyqueue[0].arrival_time)
        waiting_time += (readyqueue[0].finish_time - readyqueue[0].arrival_time - burst)


        readyqueue.pop(0)

        t+=burst



    turnaround_time = float(turnaround_time / processes_num)
    waiting_time = float(waiting_time / processes_num)

    return (history,t,turnaround_time,waiting_time)







