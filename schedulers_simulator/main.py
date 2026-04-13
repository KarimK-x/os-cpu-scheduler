import matplotlib.pyplot as plt
from Process import Process
from gantt_chart import draw_gantt
from SJF import sjf_preemptive
from round_robin import RoundRobinScheduler

processes_list = []

## ========================================================================== ##
## ============================ Helper Functions ============================ ##
## ========================================================================== ##

# Receiving inputs while avoiding negative 
# and invalid non integer inputs
def get_valid_number(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                print("Error: Please enter a positive number.")
                continue
            return value
        except ValueError:
            print("Error: That is not a valid number. Please try again.")

def get_processes(selected_algo: str):
    number_of_processes = 0
    while (not number_of_processes > 0):
        number_of_processes = get_valid_number("Enter The number of processes : ")
        if(number_of_processes <= 0):
            print("Error: please enter a valid number.")

    i = 1
    while i <= number_of_processes:
        arrival_time = get_valid_number((f"Enter the arrival time of P{i}: "))
        burst_time = get_valid_number((f"Enter the burst time of P{i}: "))
        priority = None

        if "Priority" in selected_algo:
            priority = get_valid_number("Priority Level : ")
            
        processes_list.append(Process(i, arrival_time, burst_time, priority))
        i+=1
        
def do_algo_specific_preprocessing(selected_algo : str) -> None:
    if selected_algo in "Round Robin":
        quantum = get_valid_number("Enter quantum time for round robin. Default is 4: ")
        SCHEDULER_FUNCTIONS[selected_algo] = RoundRobinScheduler(quantum).runRoundRobin

def get_the_scheduler_type():
    SCHEDULERS = {
        "0": "exit the program",
        "1": "FCFS",
        "2": "SJF (Non-Preemptive)",
        "3": "SJF (Preemptive)",
        "4": "Round Robin",
        "5": "Priority (Non-Preemptive)",
        "6": "Priority (Preemptive)",
    }

    print("Select a Scheduler:")
    print("─" * 30)
    for key, name in SCHEDULERS.items():
        print(f"  [{key}] {name}")
    print("─" * 30)

    while True:
        choice = input("Enter your choice: ")
        if choice == '0':
            print("Goodbye 😘")
            exit()
        elif choice in SCHEDULERS:
            return SCHEDULERS[choice]
        print("  Invalid choice. Enter a number from 1 to 6.")

SCHEDULER_FUNCTIONS = {
    "FCFS":                      None,
    "SJF (Non-Preemptive)":      None,
    "SJF (Preemptive)":     sjf_preemptive,
    "Round Robin":               RoundRobinScheduler().runRoundRobin,
    "Priority (Non-Preemptive)": None,
    "Priority (Preemptive)":     None,
}


## ===================================================================== ##
## ================================ Main ================================ ##
## ===================================================================== ##

def main():    
    while True:
        selected_algo = get_the_scheduler_type()
        get_processes(selected_algo)
        
        do_algo_specific_preprocessing(selected_algo)

        plt.ion() 
        fig, ax = plt.subplots(figsize=(12, 3))
        plt.show(block=False)

        run_fn = SCHEDULER_FUNCTIONS[selected_algo]
        history, time_counter, turn_around_time, average_waiting_time = run_fn(processes_list, True, fig, ax)

        print(f"\nAverage Turnaround Time : {turn_around_time:.2f} sec")
        print(f"Average Waiting Time    : {average_waiting_time:.2f} sec\n")

        plt.ioff()
        plt.close(fig)
        final_fig, final_ax = plt.subplots(figsize=(12, 3))
        draw_gantt(final_ax, history, time_counter)
        plt.show()

if __name__ == "__main__":
    main()