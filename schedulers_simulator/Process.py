class Process:
    def __init__(self, num: int, arrival_time: int, burst_time: int, 
                 priority: int | None = None):
        #General
        self.num = num
        self.arrival_time = arrival_time
        self.burst_time = burst_time

        # SJF
        self.original_arrival_time = arrival_time 
        self.priority = priority
        self.turn_around_time = 0
        self.waiting_time = 0
        
        # Round Robin (Parameters for logic, not to be input by user)
        self.isFinished : bool | None = False
        self.start_time : int | None = None
        self.finish_time : int | None = None

        #preemptive_priority
        self.original_burst_time = burst_time

    #tells heapq how to sort processes
    def __lt__(self, other): #less than
        return (self.priority, self.arrival_time, self.num) <\
                (other.priority, other.arrival_time, other.num)