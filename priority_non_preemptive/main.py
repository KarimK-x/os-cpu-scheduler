from Non_preemptive_priority import Non_Preemptive_priority_schedular

scheduler = Non_Preemptive_priority_schedular()

while True:
    try:
        no_process = int(input("Enter number of process: \n "))
        if(no_process >= 0):
            break
        else:
            print("Enter postive number\n")
    except ValueError:
            print("Invalid input\n")

for i in range(no_process):
    num = f"P{i+1}"  # ask user to enter process name
     # ask user to enter the arrival time of the process and handle invalid inputs
    while True:
        try:
            arrival_time = int(input(f"Enter the arrival time of {num}: \n "))
            if(arrival_time >=0):
                break
            else:
                print("Enter postive number\n")
        except ValueError:
                print("Invalid input\n")
     # ask user to enter the burst time of the process and handle invalid inputs       
    while True:
        try:
            burst_time = int(input(f"Enter the burst time of {num}: \n "))
            if(burst_time > 0):
                break
            else:
                print("Enter postive and non zero number\n")
        except ValueError:
                print("Invalid input\n")
     # ask user to enter the priority of the process and handle invalid inputs       
    while True:
        try:
            priority = int(input(f"Enter priority of {num}: \n "))
            if(priority >= 0):
                break
            else:
                print("Enter postive number\n")
        except ValueError:
                print("Invalid input\n")

    scheduler.add_processes(num, arrival_time, burst_time, priority)

# Run algorithm
scheduler.Non_preemptive_priority()
# Draw Gantt chart
scheduler.gantt_chart()

print("\nAverage turnaround time = ",scheduler.avg_turnaround_time())
print("\nAverage waiting time = ",scheduler.avg_waiting_time())

