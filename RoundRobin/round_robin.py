from __future__ import annotations
import time
import matplotlib.pyplot as plt
from schedulers_simulator.Process import Process

#RoundRobin Process Swapped for general Process in Integration
# class Process:
#     num : int
#     arrival_time : int
#     burst_time : int
#     isFinished : bool
#     start_time : int
#     finish_time : int
    
    
#     def __init__(self, num,arrival_time,burst_time) -> None:
#         self.num = num
#         self.arrival_time = arrival_time
#         self.burst_time = burst_time
#         self.isFinished = False

class RoundRobinScheduler:
    quantum : int
    current_time : int = 0
    process_time_ranges : list[list[tuple[int,int]]]
        
    def __init__(self, quantum = 4) -> None:
        """
        quantum (int) : Time spent on each process before switching to next. Default = 4s.
        """
        self.quantum = quantum
        
    def runRoundRobin(self, current_processes : list[Process]) -> list[list[tuple[int,int]]]:
        """
        Args:
            processes (list[Process]):  A list of Process objects
            
        Operation:
            Performs round robin scheduling and prints operation execution.
        
        Returns:
            A table of processes and their CPU Burst times.
        """
        self.process_time_ranges = [[] for _ in range(len(current_processes))]
        self.drawGant(self.process_time_ranges, live=True)
        
        # To Loop Back Again
        while(current_processes):
            print(f"============\nROUND ROBIN: Current Processes: {[process.num for process in current_processes]}")
            i=0
            while i < len(current_processes):
                process_removed_flag = False
                process = current_processes[i]
                process.start_time = self.current_time
            
                
                print("CURRENT PROCESS EXECUTING IS", process.num, "BURST TIME REMAINING:", process.burst_time)
                for t in range(self.quantum):
                    self.current_time += 1
                    time.sleep(1)
                    process.burst_time = process.burst_time - 1
                    print(f"Executing process {process.num} for {t+1} seconds. Remaining burst time: {process.burst_time}")
                    
                    self.drawGant(
                        self.process_time_ranges,
                        live=True,
                        active_segment=(process.num, process.start_time, self.current_time),
                    )

                    # Process ends before quantum is done
                    if process.burst_time <= 0: 
                        process.isFinished = True
                        print(f"PROCESS {process.num} IS FINISHED AND REMOVED")
                        
                        process.finish_time = self.current_time
                        self.process_time_ranges[process.num].append((process.start_time, process.finish_time))
                        
                        current_processes.remove(process)
                        process_removed_flag = True
                        self.drawGant(self.process_time_ranges, live=True)
                        break
                    
                # Do not increment i if a process is removed. As processes shifts down.    
                if not process_removed_flag:
                    i+=1        
                    process.finish_time = self.current_time
                    self.process_time_ranges[process.num].append((process.start_time, process.finish_time))
                    self.drawGant(self.process_time_ranges, live=True)
                
        self.drawGant(self.process_time_ranges, live=True, finalize=True)
        return self.process_time_ranges
    
    def calculateAverageWaitingTime(self, process_time_ranges):
        avg_waiting_time = 0
        for process in process_time_ranges:
            process_wait_time = process[0][0]
            for i in range(len(process)-1):
                process_wait_time += process[i+1][0] - process[i][1]
            avg_waiting_time += process_wait_time
            
        avg_waiting_time /= len(process_time_ranges)
        
        return avg_waiting_time
    
    def calculateAverageTurnAroundTime(self, process_time_ranges):
        avg_turnaround_time = 0
        for process in process_time_ranges:
            process_turnaround_time = process[-1][1] - 0
            avg_turnaround_time += process_turnaround_time
            
        avg_turnaround_time /= len(process_time_ranges)
        
        return avg_turnaround_time
            
            
    def drawGant(
        self,
        process_time_ranges: list[list[tuple[int, int]]],
        live: bool = False,
        active_segment: tuple[int, int, int] | None = None,
        finalize: bool = False,
    ) -> None:
        history: list[tuple[int, int, int]] = []
        for process_num, ranges in enumerate(process_time_ranges):
            for start, end in ranges:
                history.append((process_num, start, end))

        # Draw the currently running slice before it is committed to history.
        if active_segment is not None:
            process_num, start, end = active_segment
            if end > start:
                history.append((process_num, start, end))

        if not history:
            if live and finalize:
                fig, _ = plt.subplots(figsize=(12, 3))
                fig.savefig("RoundRobinGantt.png", dpi=150)
                plt.close(fig)
            return

        history.sort(key=lambda item: item[1])

        if live:
            if not hasattr(self, "_gantt_fig") or not hasattr(self, "_gantt_ax"):
                plt.ion()
                self._gantt_fig, self._gantt_ax = plt.subplots(figsize=(12, 3))
                plt.show(block=False)
            fig = self._gantt_fig
            ax = self._gantt_ax
            ax.clear()
        else:
            fig, ax = plt.subplots(figsize=(12, 3))
        cmap = plt.get_cmap("tab10")
        colors = [cmap(i) for i in range(10)]

        for process_num, start, end in history:
            ax.barh(
                0,
                end - start,
                left=start,
                height=0.5,
                color=colors[process_num % len(colors)],
                edgecolor="black",
            )
            ax.text(
                (start + end) / 2,
                0,
                f"P{process_num}",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="white",
            )

        boundaries = sorted({t for _, start, end in history for t in (start, end)})
        ax.set_xticks(boundaries)
        ax.set_yticks([])
        ax.set_xlabel("Time")
        ax.set_title("Gantt Chart - Round Robin")
        ax.set_xlim(0, max(end for _, _, end in history))
        plt.tight_layout()

        if live:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            plt.pause(0.001)
            if finalize:
                fig.savefig("RoundRobinGantt.png", dpi=150)
                plt.ioff()
                plt.close(fig)
                del self._gantt_fig
                del self._gantt_ax
        else:
            plt.savefig("RoundRobinGantt.png", dpi=150)
            plt.close(fig)
        
        
        
        

            
                
            
    
