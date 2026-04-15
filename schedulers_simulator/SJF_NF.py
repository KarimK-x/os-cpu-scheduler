from Process import Process
from gantt_chart import redraw_gantt
import matplotlib.pyplot as plt
import time



def sjf(processes: list[Process], new_process_queue = None, live_sim: bool = False, pause_event = None, fig = None, ax = None)->tuple[list, int, float, float]:

    readyqueue = []
    history = []
    processes_num = len(processes)
    processes_curr = processes_num
    turnaround_time = 0
    waiting_time = 0

    t = 0
    processes = sorted(processes, key=lambda x: (x.arrival_time, x.num))

    while readyqueue or processes:

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
                if pause_event:
                    pause_event.wait()
                while not new_process_queue.empty():
                    p = new_process_queue.get()
                    p.arrival_time += t
                    processes.append(p)
                    processes_curr+=1

        print(f"\n  ✔  P{readyqueue[0].num} finished at t={t+burst}")
        print(f"{'─' * 40}")


        turnaround_time += (readyqueue[0].finish_time - readyqueue[0].arrival_time)
        waiting_time += (readyqueue[0].finish_time - readyqueue[0].arrival_time - burst)


        readyqueue.pop(0)

        t+=burst



    turnaround_time = float(turnaround_time / processes_num)
    waiting_time = float(waiting_time / processes_num)

    return (history,t,turnaround_time,waiting_time)