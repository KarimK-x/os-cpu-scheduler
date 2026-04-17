#class process:
#    def __init__(self,num,arrival_time,burst_time,priority):
#        self.num          = num
#        self.arrival_time = arrival_time
#        self.burst_time   = burst_time
#        self.priority     = priority
#        
#        self.start_time = 0
#        self.finish_time = 0

from process import Process

class Non_Preemptive_priority_schedular:
        def __init__(self):
            self.job_queue       = []
            self.ready_queue     = []
            self.gantt           = []
            self.completed_queue = []
            self.current_time    = 0
        # Add processes into job queue
        def add_processes(self,num,arrival_time, burst_time, priority):
            self.job_queue.append(Process(num,arrival_time, burst_time, priority))
            
        # Algorithm operation
        def Non_preemptive_priority(self):
            
            while(len(self.job_queue) != 0 or len(self.ready_queue) != 0):   # check that all process are transfered to ready queue and executed
                # Put processes in the ready queue
                for process in self.job_queue:
                    if(self.current_time >= process.arrival_time):
                        self.ready_queue.append(process)
                        self.job_queue.remove(process)

                # Handle if the ready queue is empty by incrementing current_time by 1 second
                if(len(self.ready_queue) == 0):
                    self.current_time += 1
                    continue
                
                # Determine priority of the process if there are 2 processes have the same priority use FCFS algorithm 
                ready_process = self.ready_queue[0]
                for process in self.ready_queue:
                    if(process.priority < ready_process.priority or 
                      (process.priority == ready_process.priority and
                       process.arrival_time < ready_process.arrival_time)):
                        ready_process = process

                # execute process
                start_time   = self.current_time
                self.current_time = start_time + ready_process.burst_time # After execute process
                self.completed_queue.append((ready_process.num, start_time, self.current_time,ready_process.arrival_time,ready_process.burst_time))
                self.gantt.append((ready_process.num, start_time, self.current_time))
                self.ready_queue.remove(ready_process)
                
                return self.gantt
                
        # Draw Gantt chart      
        def gantt_chart(self):
            import matplotlib.pyplot as plt
            if(len(self.gantt) == 0):  # handle empty gantt
                print("No processes to display")
            else:
                i = 0
                while i < len(self.gantt):
                    name     = self.gantt[i][0]
                    start    = self.gantt[i][1]
                    finish   = self.gantt[i][2]
                    duration = finish - start

                    plt.barh("CPU", duration, left=start)
                    plt.text(start + duration / 2, 0, name,
                             ha="center", va="center", color="white")
                    i += 1

                max_time = self.gantt[len(self.gantt) - 1][2]  # last finish time
                plt.xticks(range(max_time + 1))
                plt.xlabel("Time")
                plt.title("Gantt Chart - Priority Scheduling")
                plt.show()         
        # calculate average waiting time
        def avg_turnaround_time(self):
            total_turnaround = 0
            for i in range(len(self.completed_queue)):
                start   = self.completed_queue[i][1]
                finish  = self.completed_queue[i][2]
                arrival = self.completed_queue[i][3]
                turnaround_time   = finish - arrival
                total_turnaround += turnaround_time

            try:
                average_turnaround_time = total_turnaround / len(self.completed_queue)
                return average_turnaround_time
            except ZeroDivisionError:
                 print("average_turnaround_time Can't be divided by zero\n")

            
        
        # calculate average waiting time
        def avg_waiting_time(self):
            total_waiting_time = 0
            for i in range(len(self.completed_queue)):
                start   = self.completed_queue[i][1]
                finish  = self.completed_queue[i][2]
                arrival = self.completed_queue[i][3]
                burst   = self.completed_queue[i][4]

                waiting_time   = finish - arrival - burst
                total_waiting_time += waiting_time

            try:
                average_waiting_time = total_waiting_time / len(self.completed_queue)
                return average_waiting_time
            except ZeroDivisionError:
                 print("average_waiting_time Can't be divided by zero\n")
            
            