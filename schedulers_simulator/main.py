import matplotlib.pyplot as plt
from Process import Process
from gantt_chart import draw_gantt
from SJF import sjf_preemptive
from round_robin import RoundRobinScheduler
from preemptive_priority import preemptive_priority_scheduler
import threading
from queue import Queue
import sys
import select

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

def get_processes(selected_algo: str, processes_list: list[Process]):
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
    if selected_algo  == "Round Robin":
        quantum = get_valid_number("Enter quantum time for round robin. Default is 4.")
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
    "SJF (Preemptive)":          sjf_preemptive,
    "Round Robin":               RoundRobinScheduler().runRoundRobin,
    "Priority (Non-Preemptive)": None,
    "Priority (Preemptive)":     preemptive_priority_scheduler,
}


def pause_event_handler(selected_algo: str, processes_list: list[Process], new_process_queue, pause_event, stop_event):
    current_id=len(processes_list)
    while not stop_event.is_set():
        
        input()

        if pause_event.is_set():
            pause_event.clear()
            print("\n Simulation is paused")
            print(" [A] : add a new process")
            print(" [R] : Resume the simulation")
            #i = 0
            while True:
                choice = input(" Choice : ").strip().upper()
                if(choice == "A"):
                    # num = len(processes_list) + i + 1
                    # i+=1
                    current_id+=1
                    num=current_id

                    print("please note the arrival time will be considered from this second")
                    arrival_time = get_valid_number((f"Enter the arrival time: "))
                    burst_time = get_valid_number((f"Enter the burst time: "))
                    priority = None

                    if "Priority" in selected_algo:
                        priority = get_valid_number("Priority Level : ")
                    
                    new_p = Process(num, arrival_time, burst_time, priority)
                    new_process_queue.put(new_p)
                    print(f" p{new_p.num} is added successfully.")
                elif(choice == "R"):
                    pause_event.set()         
                    print(" Resumed...\n")
                    break

                else: 
                    print("invalid option please try again [A] or [R]")
        else:
            pause_event.set()
            print("\n Resumed")

## ===================================================================== ##
## ================================ Main ================================ ##
## ===================================================================== ##

def main():
    while True:
        processes_list    = []        
        new_process_queue = Queue()   
        pause_event       = threading.Event()
        stop_event        = threading.Event()
        pause_event.set()

        selected_algo       = get_the_scheduler_type()
        get_processes(selected_algo, processes_list)
        do_algo_specific_preprocessing(selected_algo)

        listener = threading.Thread(
            target = pause_event_handler,
            args   = (selected_algo, processes_list, new_process_queue, pause_event, stop_event),
            daemon = True
        )
        listener.start()
        print("\n  Press Enter at any time to pause / resume.\n")

        plt.ion()
        fig, ax = plt.subplots(figsize=(12, 3))

        run_fn = SCHEDULER_FUNCTIONS[selected_algo]
        history, time_counter, awt, att = run_fn(
            processes_list,
            new_process_queue,
            live_sim    = True,
            pause_event = pause_event,
            fig         = fig,
            ax          = ax
        )

        stop_event.set()

        #need to release the input lock
        print("\n [Simulation Complete] Press 'Enter' to view the final chart...")

        listener.join()

        print(f"\nAverage Turnaround Time : {att:.2f} sec")
        print(f"Average Waiting Time    : {awt:.2f} sec\n")
        print(f"Close the chart window to continue.")

        plt.ioff()
        draw_gantt(ax, history, time_counter)
        plt.show()

if __name__ == "__main__":
    main()