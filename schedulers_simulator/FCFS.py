import Process

class FCFS:
    def __init__(self, processes):
        self.processes = sorted(processes, key=lambda p: p.arrival_time)
        self.gantt_chart = []

    def run(self):
        current_time = 0
        for p in self.processes:
            # handle CPU idle time
            if(current_time<p.arrival_time):
                self.gantt_chart.append(("IDLE", current_time, p.arrival_time))
                current_time = p.arrival_time
            p.start_time = current_time
            current_time = current_time + p.burst_time
            p.finish_time = current_time
            p.isFinished = True
            p.turnaround_time = p.finish_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            self.gantt_chart.append((p.num, p.start_time, p.finish_time))

        return self.processes, self.gantt_chart

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

    scheduler = FCFS(test_processes)
    finished_procs, gantt = scheduler.run()

    print("PID | Start | End | TAT | WT")
    print("-" * 30)
    for p in finished_procs:
        print(f"{p.num}   | {p.start_time:<5} | {p.finish_time:<3} | {p.turnaround_time:<3} | {p.waiting_time}")

    # 4. Check Averages
    avg_tat, avg_wt = scheduler.calculateAverageTime()
    print(f"\nAverage TAT: {avg_tat:.2f}")
    print(f"Average WT: {avg_wt:.2f}")
    print(f"Gantt Chart: {gantt}")