import tkinter as tk
from datetime import datetime
from collections import deque
import random

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# =========================
# DATA GLOBAL
# =========================

running = False

workers = {
    "MCU A": {
        "type": "climate",
        "data": {},
        "last_update": "-"
    },
    "MCU B": {
        "type": "soil",
        "data": {},
        "last_update": "-"
    },
    "MCU C": {
        "type": "light",
        "data": {},
        "last_update": "-"
    }
}

time_history = deque(maxlen=12)
temperature_history = deque(maxlen=12)
soil_history = deque(maxlen=12)
light_history = deque(maxlen=12)

sensor_labels = {}
time_labels = {}

root = None
sync_label = None
status_label = None
fan_label = None
pump_label = None
lamp_label = None
log_text = None

figure = None
canvas = None
ax_temp = None
ax_soil = None
ax_light = None


# =========================
# SIMULASI SENSOR
# =========================

def read_sensor(node_name):
    worker = workers[node_name]
    sensor_type = worker["type"]

    if sensor_type == "climate":
        worker["data"] = {
            "temperature": round(random.uniform(24, 38), 1),
            "air_humidity": round(random.uniform(45, 90), 1)
        }

    elif sensor_type == "soil":
        worker["data"] = {
            "soil_moisture": round(random.uniform(20, 85), 1),
            "soil_ph": round(random.uniform(5.0, 8.0), 1)
        }

    elif sensor_type == "light":
        worker["data"] = {
            "light_intensity": round(random.uniform(100, 1000), 1),
            "uv_index": round(random.uniform(0, 10), 1)
        }

    worker["last_update"] = datetime.now().strftime("%H:%M:%S")


def get_sensor_value(sensor_name):
    for node_name in workers:
        data = workers[node_name]["data"]

        if sensor_name in data:
            return data[sensor_name]

    return None


# =========================
# MASTER MCU
# =========================

def master_decision():
    temperature = get_sensor_value("temperature")
    soil_moisture = get_sensor_value("soil_moisture")
    light_intensity = get_sensor_value("light_intensity")

    if temperature is not None and temperature > 30:
        fan = "ON"
    else:
        fan = "OFF"

    if soil_moisture is not None and soil_moisture < 40:
        pump = "ON"
    else:
        pump = "OFF"

    if light_intensity is not None and light_intensity < 350:
        lamp = "ON"
    else:
        lamp = "OFF"

    if fan == "ON" or pump == "ON" or lamp == "ON":
        status = "NEED ACTION"
    else:
        status = "NORMAL"

    return status, fan, pump, lamp


# =========================
# GUI
# =========================

def create_gui():
    global root
    global sync_label
    global status_label, fan_label, pump_label, lamp_label
    global log_text
    global figure, canvas, ax_temp, ax_soil, ax_light

    root = tk.Tk()
    root.title("Greenhouse Distributed Control")
    root.geometry("1060x620")
    root.resizable(False, False)
    root.configure(bg="#0b1220")

    # HEADER
    header = tk.Frame(root, bg="#0b1220")
    header.pack(fill="x", padx=18, pady=(12, 8))

    title = tk.Label(
        header,
        text="Greenhouse Distributed Control",
        font=("Segoe UI", 16, "bold"),
        bg="#0b1220",
        fg="#e2e8f0"
    )
    title.pack(side="left")

    sync_label = tk.Label(
        header,
        text="Waiting for data...",
        font=("Segoe UI", 8),
        bg="#0b1220",
        fg="#94a3b8"
    )
    sync_label.pack(side="right", pady=(6, 0))

    # MAIN
    main = tk.Frame(root, bg="#0b1220")
    main.pack(fill="both", expand=True, padx=18, pady=(0, 14))

    left = tk.Frame(main, bg="#0b1220", width=610)
    left.pack(side="left", fill="both")
    left.pack_propagate(False)

    right = tk.Frame(main, bg="#101827", width=410)
    right.pack(side="right", fill="both", padx=(14, 0))
    right.pack_propagate(False)

    create_sensor_area(left)
    create_master_area(left)
    create_graph_area(left)
    create_log_area(right)


def create_sensor_area(parent):
    sensor_frame = tk.Frame(parent, bg="#0b1220")
    sensor_frame.pack(fill="x", pady=(0, 10))

    create_sensor_card(
        sensor_frame,
        "MCU A",
        "CLIMATE NODE",
        "#0f766e",
        [
            ("temperature", "Temp", "°C"),
            ("air_humidity", "Air Hum", "%")
        ],
        0
    )

    create_sensor_card(
        sensor_frame,
        "MCU B",
        "SOIL NODE",
        "#7c3aed",
        [
            ("soil_moisture", "Soil", "%"),
            ("soil_ph", "pH", "")
        ],
        1
    )

    create_sensor_card(
        sensor_frame,
        "MCU C",
        "LIGHT NODE",
        "#ca8a04",
        [
            ("light_intensity", "Light", "lux"),
            ("uv_index", "UV", "")
        ],
        2
    )


def create_sensor_card(parent, node_name, title, color, sensors, column):
    card = tk.Frame(
        parent,
        bg="#101827",
        highlightbackground="#263244",
        highlightthickness=1,
        width=192,
        height=116
    )
    card.grid(row=0, column=column, padx=(0 if column == 0 else 10, 0))
    card.grid_propagate(False)

    color_bar = tk.Frame(card, bg=color, height=4)
    color_bar.pack(fill="x")

    top = tk.Frame(card, bg="#101827")
    top.pack(fill="x", padx=10, pady=(7, 2))

    title_label = tk.Label(
        top,
        text=title,
        font=("Segoe UI", 9, "bold"),
        bg="#101827",
        fg="#e2e8f0"
    )
    title_label.pack(side="left")

    time_label = tk.Label(
        top,
        text="--:--",
        font=("Segoe UI", 7),
        bg="#101827",
        fg="#64748b"
    )
    time_label.pack(side="right")

    time_labels[node_name] = time_label

    value_frame = tk.Frame(card, bg="#101827")
    value_frame.pack(fill="x", padx=10, pady=(6, 0))

    index = 0

    for sensor in sensors:
        sensor_key = sensor[0]
        sensor_name = sensor[1]
        sensor_unit = sensor[2]

        box = tk.Frame(value_frame, bg="#162235")
        box.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 6, 0))
        value_frame.grid_columnconfigure(index, weight=1)

        name_label = tk.Label(
            box,
            text=sensor_name,
            font=("Segoe UI", 7),
            bg="#162235",
            fg="#94a3b8"
        )
        name_label.pack(anchor="w", padx=7, pady=(5, 0))

        value_label = tk.Label(
            box,
            text="-",
            font=("Segoe UI", 11, "bold"),
            bg="#162235",
            fg="#f8fafc"
        )
        value_label.pack(anchor="w", padx=7, pady=(0, 5))

        sensor_labels[sensor_key] = {
            "label": value_label,
            "unit": sensor_unit
        }

        index += 1


def create_master_area(parent):
    global status_label, fan_label, pump_label, lamp_label

    console = tk.Frame(
        parent,
        bg="#101827",
        highlightbackground="#263244",
        highlightthickness=1
    )
    console.pack(fill="x", pady=(0, 10))

    top = tk.Frame(console, bg="#101827")
    top.pack(fill="x", padx=12, pady=(10, 8))

    title = tk.Label(
        top,
        text="MASTER CONTROLLER",
        font=("Segoe UI", 10, "bold"),
        bg="#101827",
        fg="#e2e8f0"
    )
    title.pack(side="left")

    status_label = tk.Label(
        top,
        text="IDLE",
        font=("Segoe UI", 8, "bold"),
        bg="#334155",
        fg="#f8fafc",
        padx=10,
        pady=4
    )
    status_label.pack(side="right")

    output_frame = tk.Frame(console, bg="#101827")
    output_frame.pack(fill="x", padx=12, pady=(0, 10))

    fan_label = create_output_box(output_frame, "Kipas", "OFF", 0)
    pump_label = create_output_box(output_frame, "Pompa Air", "OFF", 1)
    lamp_label = create_output_box(output_frame, "Grow Light", "OFF", 2)

    button_frame = tk.Frame(console, bg="#101827")
    button_frame.pack(fill="x", padx=12, pady=(0, 12))

    start_button = tk.Button(
        button_frame,
        text="RUN",
        font=("Segoe UI", 8, "bold"),
        bg="#22c55e",
        fg="#052e16",
        relief="flat",
        padx=12,
        pady=6,
        command=start_simulation
    )
    start_button.pack(side="left", fill="x", expand=True, padx=(0, 6))

    stop_button = tk.Button(
        button_frame,
        text="PAUSE",
        font=("Segoe UI", 8, "bold"),
        bg="#f59e0b",
        fg="#451a03",
        relief="flat",
        padx=12,
        pady=6,
        command=stop_simulation
    )
    stop_button.pack(side="left", fill="x", expand=True, padx=6)

    reset_button = tk.Button(
        button_frame,
        text="CLEAR GRAPH",
        font=("Segoe UI", 8, "bold"),
        bg="#ef4444",
        fg="#450a0a",
        relief="flat",
        padx=12,
        pady=6,
        command=reset_graph
    )
    reset_button.pack(side="left", fill="x", expand=True, padx=(6, 0))


def create_output_box(parent, name, value, column):
    box = tk.Frame(parent, bg="#162235")
    box.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
    parent.grid_columnconfigure(column, weight=1)

    name_label = tk.Label(
        box,
        text=name,
        font=("Segoe UI", 8),
        bg="#162235",
        fg="#94a3b8"
    )
    name_label.pack(anchor="w", padx=9, pady=(7, 0))

    value_label = tk.Label(
        box,
        text=value,
        font=("Segoe UI", 12, "bold"),
        bg="#162235",
        fg="#f87171"
    )
    value_label.pack(anchor="w", padx=9, pady=(0, 7))

    return value_label


def create_graph_area(parent):
    global figure, canvas, ax_temp, ax_soil, ax_light

    panel = tk.Frame(
        parent,
        bg="#101827",
        highlightbackground="#263244",
        highlightthickness=1
    )
    panel.pack(fill="both", expand=True)

    title = tk.Label(
        panel,
        text="SENSOR GRAPH MONITOR",
        font=("Segoe UI", 10, "bold"),
        bg="#101827",
        fg="#e2e8f0"
    )
    title.pack(anchor="w", padx=12, pady=(8, 0))

    figure = Figure(figsize=(5.6, 2.85), dpi=100)
    figure.patch.set_facecolor("#101827")

    ax_temp = figure.add_subplot(131)
    ax_soil = figure.add_subplot(132)
    ax_light = figure.add_subplot(133)

    canvas = FigureCanvasTkAgg(figure, master=panel)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)


def create_log_area(parent):
    global log_text

    title = tk.Label(
        parent,
        text="DISTRIBUTED NODE LOG",
        font=("Segoe UI", 12, "bold"),
        bg="#101827",
        fg="#e2e8f0"
    )
    title.pack(anchor="w", padx=14, pady=(12, 2))

    subtitle = tk.Label(
        parent,
        text="Worker MCU packet history",
        font=("Segoe UI", 8),
        bg="#101827",
        fg="#64748b"
    )
    subtitle.pack(anchor="w", padx=14, pady=(0, 6))

    log_text = tk.Text(
        parent,
        font=("Consolas", 9),
        bg="#020617",
        fg="#d1fae5",
        insertbackground="#f8fafc",
        relief="flat",
        wrap="word"
    )
    log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))


# =========================
# UPDATE GUI
# =========================

def start_simulation():
    global running

    if running == False:
        running = True
        add_log("SYSTEM", "simulation started")
        run_simulation()


def stop_simulation():
    global running

    running = False
    add_log("SYSTEM", "simulation paused")


def run_simulation():
    if running == False:
        return

    for node_name in workers:
        read_sensor(node_name)
        add_log(node_name, "packet sent to Master MCU")

    status, fan, pump, lamp = master_decision()

    update_dashboard(status, fan, pump, lamp)
    update_history()
    draw_graph()

    root.after(1200, run_simulation)


def update_dashboard(status, fan, pump, lamp):
    now = datetime.now().strftime("%H:%M:%S")
    sync_label.config(text=f"Last sync: {now}")

    for node_name in workers:
        time_labels[node_name].config(text=workers[node_name]["last_update"])

    for node_name in workers:
        data = workers[node_name]["data"]

        for sensor_key in data:
            value = data[sensor_key]
            unit = sensor_labels[sensor_key]["unit"]
            label = sensor_labels[sensor_key]["label"]

            label.config(text=f"{value} {unit}")

    if status == "NORMAL":
        status_label.config(text="NORMAL", bg="#15803d")
    else:
        status_label.config(text="NEED ACTION", bg="#b45309")

    update_output_label(fan_label, fan)
    update_output_label(pump_label, pump)
    update_output_label(lamp_label, lamp)


def update_output_label(label, value):
    if value == "ON":
        label.config(text="ON", fg="#86efac")
    else:
        label.config(text="OFF", fg="#f87171")


def update_history():
    now = datetime.now().strftime("%H:%M:%S")

    temperature = get_sensor_value("temperature")
    soil_moisture = get_sensor_value("soil_moisture")
    light_intensity = get_sensor_value("light_intensity")

    if temperature is not None and soil_moisture is not None and light_intensity is not None:
        time_history.append(now)
        temperature_history.append(temperature)
        soil_history.append(soil_moisture)
        light_history.append(light_intensity)


def style_graph(axis, title, ylabel):
    axis.set_facecolor("#101827")
    axis.set_title(title, fontsize=8, color="#e2e8f0")
    axis.set_ylabel(ylabel, fontsize=7, color="#94a3b8")
    axis.tick_params(axis="x", rotation=35, labelsize=5, colors="#94a3b8")
    axis.tick_params(axis="y", labelsize=6, colors="#94a3b8")
    axis.grid(True, alpha=0.22)

    for line in axis.spines.values():
        line.set_color("#334155")


def draw_graph():
    ax_temp.clear()
    ax_soil.clear()
    ax_light.clear()

    times = list(time_history)

    ax_temp.plot(times, list(temperature_history), marker="o", markersize=2.5)
    style_graph(ax_temp, "Temp", "°C")

    ax_soil.plot(times, list(soil_history), marker="o", markersize=2.5)
    style_graph(ax_soil, "Soil", "%")

    ax_light.plot(times, list(light_history), marker="o", markersize=2.5)
    style_graph(ax_light, "Light", "lux")

    figure.tight_layout(pad=1.1)
    canvas.draw()


def add_log(source, message):
    now = datetime.now().strftime("%H:%M:%S")
    log_text.insert(tk.END, f"[{now}] {source:<10} | {message}\n")
    log_text.see(tk.END)


def reset_graph():
    time_history.clear()
    temperature_history.clear()
    soil_history.clear()
    light_history.clear()

    add_log("MASTER", "graph buffer cleared")
    draw_graph()


# =========================
# MAIN PROGRAM
# =========================

create_gui()
root.mainloop()