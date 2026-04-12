import matplotlib.pyplot as plt
from Process import Process

processes_list = []
history = []
time_counter = 0
number_of_processes = 0
selected_algo = None

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

def get_processes():
    number_of_processes = get_valid_number("Enter The number of processes : ")
    i = 1
    while i <= number_of_processes:
        arrival_time = get_valid_number((f"Enter the arrival time of P{i}: "))
        burst_time = get_valid_number((f"Enter the burst time of P{i}: "))
        priority = None

        if "Priority" in selected_algo:
            priority = get_valid_number("Priority Level : ")
            
        processes_list.append(Process(i, arrival_time, burst_time, priority))
        i+=1

def get_the_scheduler_type():
    pass




## ===================================================================== ##
## ============================ Gantt Chart ============================ ##
## ===================================================================== ##
fig, ax = plt.subplots(figsize=(12, 3))
colors = plt.cm.tab10.colors

for (pnum, start, end) in history:
    ax.barh(0, end - start, left=start, height=0.5,
            color=colors[(pnum - 1) % len(colors)],
            edgecolor="black")
    ax.text((start + end) / 2, 0, f"P{pnum}",
            ha="center", va="center", fontsize=9,
            fontweight="bold", color="white")

boundaries = sorted(set(t for _, s, e in history for t in (s, e)))
ax.set_xticks(boundaries)
ax.set_yticks([])
ax.set_xlabel("Time")
ax.set_title("Gantt Chart — SJF Preemptive")
ax.set_xlim(0, time_counter)
plt.tight_layout()
plt.savefig("gantt.png", dpi=150)
plt.show()