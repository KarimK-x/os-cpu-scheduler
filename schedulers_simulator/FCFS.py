import Process
from gantt_chart import redraw_gantt
import time

class FCFS:
    def __init__(self):
        pass

    def run(self, processes : list[Process], live_sim : bool = False, fig = None, ax = None):
        self.processes = sorted(processes, key=lambda p: p.arrival_time)
        self.gantt_chart = []
        current_time = 0

        if live_sim:
            for p in self.processes:
                if current_time < p.arrival_time:
                    idle_start = current_time
                    self.gantt_chart.append([0, idle_start, idle_start + 1])
                    while current_time < p.arrival_time:
                        time.sleep(1)
                        current_time += 1
                        self.gantt_chart[-1][2] = current_time
                        redraw_gantt(ax, self.gantt_chart)
                        fig.canvas.draw()
                        fig.canvas.flush_events()

                p.start_time = current_time
                self.gantt_chart.append([p.num, p.start_time, p.start_time+1])
                time.sleep(1)
                redraw_gantt(ax, self.gantt_chart)
                fig.canvas.draw()
                fig.canvas.flush_events()
                for _ in range(1,p.burst_time):
                    time.sleep(1)
                    current_time += 1
                    self.gantt_chart[-1][2] += 1
                    redraw_gantt(ax,self.gantt_chart)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                current_time += 1
                p.finish_time = current_time
                p.turnaround_time = p.finish_time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.burst_time

        else:
            for p in self.processes:
                if current_time < p.arrival_time:
                    self.gantt_chart.append([0, current_time, p.arrival_time])
                    current_time = p.arrival_time
                p.start_time = current_time
                current_time = current_time + p.burst_time
                p.finish_time = current_time
                p.isFinished = True
                p.turnaround_time = p.finish_time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.burst_time
                self.gantt_chart.append([p.num, p.start_time, p.finish_time])

        avg_tat, avg_wt = self.calculateAverageTime()
        return self.gantt_chart, current_time, avg_tat, avg_wt

    def calculateAverageTime(self):
        total_tat = sum(p.turnaround_time for p in self.processes)
        total_wt = sum(p.waiting_time for p in self.processes)
        num_processes = len(self.processes)
        avg_tat = total_tat / num_processes
        avg_wt = total_wt / num_processes
        return avg_tat, avg_wt


if __name__ == "__main__":

    test_processes = [
        Process.Process(num=1, arrival_time=0, burst_time=7),
        Process.Process(num=2, arrival_time=9, burst_time=5),
        Process.Process(num=3, arrival_time=10, burst_time=3)
    ]

    scheduler = FCFS()
    gantt, current_time, avg_tat, avg_wt = scheduler.run(test_processes)

    print(f"\nGantt Chart: {gantt}")
    print(f"Average TAT: {avg_tat:.2f}")
    print(f"Average WT: {avg_wt:.2f}")

