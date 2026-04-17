from Process import Process
from gantt_chart import redraw_gantt
import time

class FCFS:
    def run(self, processes_queue : list[Process],
            new_process_queue = None,
            pause_event = None,
            live_sim : bool = False,
            fig = None, ax = None,
            on_progress = None):
        processes = sorted(processes_queue, key=lambda p:(p.arrival_time, p.num))
        gantt_chart = []
        current_time = 0
        current_p = None

        while not all(p.isFinished for p in processes) or (new_process_queue and not new_process_queue.empty()):
            if live_sim:
                if pause_event:
                    pause_event.wait()
                if new_process_queue:
                    while not new_process_queue.empty():
                        new_p = new_process_queue.get()
                        new_p.arrival_time += current_time
                        processes.append(new_p)
                        processes.sort(key=lambda p: (p.arrival_time, p.num))

                if current_p is None:
                    current_p = next((p for p in processes if not p.isFinished and current_time >= p.arrival_time),
                                     None)
                    if current_p and current_p.start_time is None:
                        current_p.start_time = current_time

                if current_p:
                    if gantt_chart and gantt_chart[-1][0] == current_p.num:
                        gantt_chart[-1][2] = current_time + 1
                    else:
                        gantt_chart.append([current_p.num, current_time, current_time + 1])

                    current_p.burst_time -= 1

                    if current_p.burst_time == 0:
                        current_p.finish_time = current_time + 1
                        current_p.isFinished = True
                        current_p.turn_around_time = current_p.finish_time - current_p.arrival_time
                        current_p.waiting_time = current_p.turn_around_time - current_p.original_burst_time
                        current_p = None
                else:
                    if gantt_chart and gantt_chart[-1][0] == 0:
                        gantt_chart[-1][2] = current_time + 1
                    else:
                        gantt_chart.append([0, current_time, current_time + 1])

                time.sleep(1)
                current_time += 1
                if fig is not None and ax is not None:
                    redraw_gantt(ax, gantt_chart)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                if on_progress is not None:
                    on_progress(gantt_chart, current_time)
            else:
                for p in processes:
                    if current_time < p.arrival_time:
                        gantt_chart.append([0, current_time, p.arrival_time])
                        current_time = p.arrival_time
                    p.start_time = current_time
                    current_time = current_time + p.burst_time
                    p.finish_time = current_time
                    p.isFinished = True
                    p.turn_around_time = p.finish_time - p.arrival_time
                    p.waiting_time = p.turn_around_time - p.burst_time
                    gantt_chart.append([p.num, p.start_time, p.finish_time])

        avg_tat, avg_wt = self.calculateAverageTime(processes)
        return gantt_chart, current_time, avg_tat, avg_wt


    def calculateAverageTime(self, processes : list):
        total_tat = sum(p.turn_around_time for p in processes)
        total_wt = sum(p.waiting_time for p in processes)
        num_processes = len(processes)
        avg_tat = total_tat / num_processes
        avg_wt = total_wt / num_processes
        return avg_tat, avg_wt