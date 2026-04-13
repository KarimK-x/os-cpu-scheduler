import matplotlib.pyplot as plt

COLORS = [
    "#E63946", "#2A9D8F", "#E9C46A", "#457B9D",
    "#F4A261", "#6A4C93", "#2DC653", "#E76F51",
]

def redraw_gantt(ax, history):
    """Called every tick during live simulation."""
    ax.clear()
    _draw_bars(ax, history)
    ax.set_title("Gantt Chart — Live")

def draw_gantt(ax, history, time_counter, title="Gantt Chart"):
    """Called once at the end for the final chart."""
    _draw_bars(ax, history)
    ax.set_xlim(0, time_counter)
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig("gantt.png", dpi=150)

def _draw_bars(ax, history):
    """Shared drawing logic — not called directly."""
    for (pnum, start, end) in history:
        color = COLORS[(pnum - 1) % len(COLORS)]
        ax.barh(0, end - start, left=start, height=0.5,
                color=color, edgecolor="white", linewidth=1.5)
        ax.text((start + end) / 2, 0, f"P{pnum}",
                ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
    boundaries = sorted(set(t for _, s, e in history for t in (s, e)))
    ax.set_xticks(boundaries)
    ax.set_yticks([])
    ax.set_xlabel("Time")