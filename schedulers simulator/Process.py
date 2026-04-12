class Process:
    def __init__(self, num: int, arrival_time: int, burst_time: int, priority: int | None = None):
        self.num = num
        self.arrival_time = arrival_time
        self.original_arrival_time = arrival_time 
        self.burst_time = burst_time
        self.priority = priority
        self.turn_around_time = 0
        self.waiting_time = 0