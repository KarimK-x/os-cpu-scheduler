from __future__ import annotations
import time
import matplotlib.pyplot as plt
from collections import defaultdict
from Process import Process
from gantt_chart import redraw_gantt

class RoundRobinScheduler:
    quantum : int
    current_time : int = 0
    process_time_ranges : list[tuple[int,int,int]]
    processes : list[Process]
        
    def __init__(self, quantum = 4) -> None:
        """
        quantum (int) : Time spent on each process before switching to next. Default = 4s.
        """
        self.quantum = quantum

    def _live_redraw(self, ax, history: list[tuple[int, int, int]]) -> None:
        """Redraw and pump GUI events so the window remains responsive."""
        if ax is None:
            return
        redraw_gantt(ax, history)
        fig = ax.figure
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        plt.pause(0.001)
        
    def runRoundRobin(self, current_processes : list[Process], new_process_queue = None,
                      live_sim: bool = False, pause_event = None , fig = None, ax = None, on_progress = None) -> tuple[list, int, float, float]:
        """
        Args:
            processes (list[Process]):  A list of Process objects
            
        Operation:
            Performs round robin scheduling and prints operation execution.
        
        Returns:
            A table of processes and their CPU Burst times.
        """
        self.process_time_ranges = []
        self.current_time = 0
        self.processes = current_processes.copy()
        if live_sim:
            self._live_redraw(ax, self.process_time_ranges)
            if on_progress is not None:
                on_progress(self.process_time_ranges, self.current_time)
        unarrived_processes : list[Process] = []
        
        # To Loop Back Again
        while(current_processes or unarrived_processes):
            if live_sim:
                if pause_event:
                    pause_event.wait()
                
            if new_process_queue:
                while not new_process_queue.empty():
                    new_p = new_process_queue.get()
                    # new_p.original_arrival_time = new_p.arrival_time + self.current_time 
                    current_processes.append(new_p)
                    self.processes.append(new_p)
                    print(f"\n [+] P{new_p.num} joined the simulation!")

            
            for process in current_processes.copy():
                if process.arrival_time > self.current_time:
                    if current_processes:
                        current_processes.remove(process)
                    unarrived_processes.append(process)
                    unarrived_processes.sort(key=lambda p: (p.arrival_time, p.num))
                    
            for process in unarrived_processes.copy():
                if process.arrival_time <= self.current_time:
                    if unarrived_processes:
                        unarrived_processes.remove(process)
                    current_processes.append(process)
                        
            print(f"============\nROUND ROBIN: Current Processes: {[process.num for process in current_processes]}")
            if current_processes:
                i=0
                while i < len(current_processes):
                    process_removed_flag = False
                    process = current_processes[i]
                    process.start_time = self.current_time
                    
                    print("CURRENT PROCESS EXECUTING IS", process.num, "BURST TIME REMAINING:", process.burst_time)
                    for t in range(self.quantum):
                        self.current_time += 1
                        if live_sim:
                            if pause_event:
                                pause_event.wait()
                            if ax is not None:
                                plt.pause(1)
                            else:
                                time.sleep(1)
                        process.burst_time -= 1
                        print(f"Executing process {process.num} for {t+1} seconds. Remaining burst time: {process.burst_time}")
                        
                        if live_sim:
                            active_history = self.process_time_ranges.copy()
                            if self.current_time > process.start_time:
                                active_history.append((process.num, process.start_time, self.current_time))
                            self._live_redraw(ax, active_history)
                            if on_progress is not None:
                                on_progress(active_history, self.current_time)

                        # Process ends before quantum is done
                        if process.burst_time <= 0: 
                            process.isFinished = True
                            print(f"PROCESS {process.num} IS FINISHED AND REMOVED")
                            
                            process.finish_time = self.current_time
                            self.process_time_ranges.append((process.num,process.start_time, process.finish_time))
                            
                            current_processes.remove(process)
                            process_removed_flag = True
                            if live_sim:
                                self._live_redraw(ax, self.process_time_ranges)
                                if on_progress is not None:
                                    on_progress(self.process_time_ranges, self.current_time)
                            break
                        
                    # Do not increment i if a process is removed. As processes shifts down.    
                    if not process_removed_flag:
                        i+=1        
                        process.finish_time = self.current_time
                        self.process_time_ranges.append((process.num, process.start_time, process.finish_time))
                        if live_sim:
                            self._live_redraw(ax, self.process_time_ranges)
                            if on_progress is not None:
                                on_progress(self.process_time_ranges, self.current_time)
            else:
                if live_sim:
                    if ax is not None:
                        plt.pause(1)
                    else:
                        time.sleep(1)
                self.current_time += 1    
                if live_sim and on_progress is not None:
                    on_progress(self.process_time_ranges, self.current_time)
        if live_sim:    
            self._live_redraw(ax, self.process_time_ranges)
            if on_progress is not None:
                on_progress(self.process_time_ranges, self.current_time)
        
        return (self.process_time_ranges,
                self.current_time,
                self.calculateAverageTurnAroundTime(self.process_time_ranges),
                self.calculateAverageWaitingTime(self.process_time_ranges))
    

    def calculateAverageWaitingTime(self, process_time_ranges: list[tuple[int, int, int]]) -> float:
        # Group segments by process number
        segments_by_process: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for process_num, start, end in process_time_ranges:
            segments_by_process[process_num].append((start, end))

        arrival_times = {p.num: p.arrival_time for p in self.processes}

        total_waiting = 0.0
        for process_num, segments in segments_by_process.items():
            segments.sort(key=lambda s: s[0])  # sort by start time

            arrival = arrival_times[process_num]

            # Wait before first execution
            waiting = segments[0][0] - arrival
            # Gaps between consecutive segments (preemption gaps)
            for i in range(1, len(segments)):
                waiting += segments[i][0] - segments[i - 1][1]
            total_waiting += waiting

        return total_waiting / len(segments_by_process)


    def calculateAverageTurnAroundTime(self, process_time_ranges: list[tuple[int, int, int]]) -> float:
        # Group segments by process number
        segments_by_process: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for process_num, start, end in process_time_ranges:
            segments_by_process[process_num].append((start, end))

        arrival_times = {p.num: p.arrival_time for p in self.processes}

        total_turnaround = 0.0
        for process_num, segments in segments_by_process.items():
            segments.sort(key=lambda s: s[0])

            last_end = segments[-1][1]
            arrival = arrival_times[process_num]

            total_turnaround += last_end - arrival

        return total_turnaround / len(segments_by_process)
            
            
    def drawGant(
        self,
        process_time_ranges: list[tuple[int,int, int]],
        live: bool = False,
        active_segment: tuple[int, int, int] | None = None,
        finalize: bool = False,
    ) -> None:
        history: list[tuple[int, int, int]] = process_time_ranges.copy()

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
        
        
        
        

            
                
            
    
