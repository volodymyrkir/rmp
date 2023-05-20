import datetime

from flask import Flask, render_template, request, jsonify
import random
import sqlite3
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from multiprocessing import Process
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

LOWER_THRESHOLD = 23.1
UPPER_THRESHOLD = 24.1


class Threshold:
    def __init__(self, value):
        self.value = value

    def set(self, value):
        self.value = value


upper_threshold = Threshold(UPPER_THRESHOLD)
lower_threshold = Threshold(LOWER_THRESHOLD)


class TkinterWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("870x670")
        self.window.title('Volodymyr Kiriushyn')
        self.fig, self.ax = plt.subplots()
        self.lines = {}
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature')
        self.ax.set_title('Temperature History')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.upper = upper_threshold
        self.lower = lower_threshold
        upper_label = tk.Label(self.window, text="Upper Threshold:")
        lower_label = tk.Label(self.window, text="Lower Threshold:")

        # Create input fields and button
        self.upper_entry = tk.Entry(self.window)
        self.lower_entry = tk.Entry(self.window)
        self.update_button = tk.Button(self.window, text="Update Thresholds", command=self.update_thresholds)

        # Position the labels, input fields, and button
        upper_label.pack(side=tk.TOP, padx=10, pady=3)
        self.upper_entry.pack(side=tk.TOP, padx=10, pady=10)
        lower_label.pack(side=tk.TOP, padx=10, pady=3)
        self.lower_entry.pack(side=tk.TOP, padx=10, pady=10)
        self.update_button.pack(side=tk.TOP, padx=10, pady=10)

        self.upper_threshold_line = None
        self.lower_threshold_line = None

    def animate(self, i):
        conn = sqlite3.connect('temperatures.db')
        c = conn.cursor()
        c.execute("SELECT * FROM temperatures ORDER BY time DESC LIMIT 30")
        data_temps = c.fetchall()
        c.execute("SELECT * FROM thresholds ORDER BY time DESC LIMIT 1")
        data_thresholds = c.fetchone()
        conn.close()

        room_numbers = set([row[1] for row in data_temps])
        self.update_lines(room_numbers)

        for room_number in room_numbers:
            x_data = [mdates.datestr2num(row[0]) for row in data_temps if row[1] == room_number]
            y_data = [row[2] for row in data_temps if row[1] == room_number]
            self.lines[room_number].set_data(x_data, y_data)

        self.ax.relim()
        self.ax.autoscale_view()
        self.update_threshold_lines(data_thresholds)
        self.fig.canvas.draw()

    def update_thresholds(self):
        lower = float(self.lower_entry.get())
        upper = float(self.upper_entry.get())

        conn = sqlite3.connect('temperatures.db')
        c = conn.cursor()
        c.execute("INSERT INTO thresholds (lower, upper) VALUES (?, ?)", (lower, upper))
        conn.commit()
        conn.close()

        self.lower.set(lower)
        self.upper.set(upper)

    def update_threshold_lines(self, data_thresholds):
        if self.upper_threshold_line:
            self.upper_threshold_line.remove()
        if self.lower_threshold_line:
            self.lower_threshold_line.remove()

        self.upper_threshold_line = None
        self.lower_threshold_line = None

        self.upper_threshold_line = self.ax.axhline(y=data_thresholds[2], color='red', linestyle='--',
                                                    label='Upper Threshold')

        self.lower_threshold_line = self.ax.axhline(y=data_thresholds[1], color='blue', linestyle='--',
                                                    label='Lower Threshold')

        self.ax.legend()

    def update_lines(self, room_numbers):
        existing_rooms = set(self.lines.keys())
        new_rooms = room_numbers - existing_rooms
        for room_number in new_rooms:
            color = self.get_random_color()
            line, = self.ax.plot([], [], '-', color=color, label=f'Room {room_number}')
            self.lines[room_number] = line
        self.ax.legend()

    @staticmethod
    def get_random_color():
        r = random.random()
        g = random.random()
        b = random.random()
        return r, g, b

    def start(self):
        conn = sqlite3.connect('temperatures.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS temperatures('
                  'time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, room INTEGER, temperature FLOAT)')
        c.execute('CREATE TABLE IF NOT EXISTS thresholds('
                  'time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, lower FLOAT, upper FLOAT)')
        c.execute('INSERT INTO thresholds (lower, upper) VALUES (?, ?)', (self.lower.value, self.upper.value))
        conn.commit()
        conn.close()
        self.animation_loop()
        self.window.mainloop()

    def animation_loop(self):
        self.animation = FuncAnimation(self.fig, self.animate, interval=4500)
        self.canvas.draw()


TEMPS = random.sample(range(11, 30), 3)


class Temperature:
    def __init__(self, room):
        self.room = room
        self.current_temperature = TEMPS[room - 1]
        self.is_heating = True
        self.change_rate = 0.6

    def change_temperature(self, lower, upper):
        if self.is_heating and self.current_temperature < upper:
            self.current_temperature = round(self.current_temperature + self.change_rate, 2)
        elif not self.is_heating and self.current_temperature >= lower:
            self.current_temperature = round(self.current_temperature - self.change_rate, 2)
        else:
            self.is_heating = not self.is_heating


temp_1 = Temperature(1)
temp_2 = Temperature(2)
temp_3 = Temperature(3)

TEMPERATURES = [temp_1, temp_2, temp_3]

app = Flask(__name__)

conn = sqlite3.connect('temperatures.db')
c = conn.cursor()

lights = {
    'light_1': True,
    'light_2': False,
    'light_3': False,
}

brightness = {
    'brightness_1': 50,
    'brightness_2': 0,
    'brightness_3': 0,
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/light')
def light():
    return render_template('index2.html', **lights, **brightness)


def change_temperatures(lower, upper):
    for temp in TEMPERATURES:
        temp.change_temperature(lower, upper)


@app.route('/temperatures')
def get_temperatures():
    conn = sqlite3.connect('temperatures.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM temperatures")
    record_count = c.fetchone()[0]

    if record_count > 100:
        c.execute("DELETE FROM temperatures WHERE time IN (SELECT time FROM temperatures ORDER BY time ASC LIMIT 50)")
    c.execute("SELECT * FROM thresholds ORDER BY time DESC LIMIT 1")
    data_thresholds = c.fetchone()
    if data_thresholds:
        change_temperatures(data_thresholds[1], data_thresholds[2])
    else:
        change_temperatures(lower_threshold.value, upper_threshold.value)
    insert_temperatures(c, TEMPERATURES)
    conn.commit()
    conn.close()
    for temp in TEMPERATURES:
        print(f'Temperature in room {temp.room} is now {temp.current_temperature}')
    return jsonify({'temperatures': [temp.current_temperature for temp in TEMPERATURES]})


@app.route('/temperatures_graph')
def get_temperatures_list():
    conn = sqlite3.connect('temperatures.db')
    c = conn.cursor()
    c.execute("SELECT * FROM temperatures WHERE room = 1 order by time DESC LIMIT 10")
    temp_list1 = list(reversed([row[2] for row in c.fetchall()]))
    c.execute("SELECT * FROM temperatures WHERE room = 2 order by time DESC LIMIT 10")
    temp_list2 = list(reversed([row[2] for row in c.fetchall()]))
    c.execute("SELECT * FROM temperatures WHERE room = 3 order by time DESC LIMIT 10")
    data = c.fetchall()
    temp_list3 = list(reversed([row[2] for row in data]))
    dates = list(
        reversed([datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S') for row in data]))
    c.execute("SELECT * FROM thresholds ORDER BY time DESC LIMIT 1")
    thresholds = c.fetchone()
    low_thr, upr_thr = thresholds[1], thresholds[2]
    conn.close()
    return jsonify({'temp_list1': temp_list1,
                    'temp_list2': temp_list2,
                    'temp_list3': temp_list3,
                    'lower_threshold': low_thr,
                    'upper_threshold': upr_thr,
                    'dates': dates})


@app.route('/toggle_light', methods=['POST'])
def toggle_light():
    data = request.get_json()
    light = data['light']
    print(f'Changing {light} in room {light.split("_")[1]} to state {not lights[light]}')
    lights[light] = not lights[light]
    return jsonify({'status': 'success'})


def insert_temperatures(c, temperatures: list):
    for temperature in temperatures:
        c.execute("INSERT INTO temperatures(room, temperature) VALUES (?, ?)",
                  (temperature.room, temperature.current_temperature))


@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    data = request.json
    print(f'Setting brightness in room {data["brightness"]} to {data["value"]}')
    brightness[data['brightness']] = int(data['value'])
    return 'OK'


@app.route('/js_thresholds', methods=['POST'])
def js_thresholds():
    data = request.get_json()
    conn = sqlite3.connect('temperatures.db')
    c = conn.cursor()
    lower_js_threshold = float(data.get('lowerThreshold'))
    upper_js_threshold = float(data.get('upperThreshold'))
    c.execute('INSERT INTO thresholds(lower, upper) VALUES (?, ?)', (lower_js_threshold, upper_js_threshold))
    conn.commit()
    conn.close()
    return jsonify(message='Thresholds updated successfully')


def start_flask():
    app.run(port=8080)


if __name__ == '__main__':
    flask_process = Process(target=start_flask)
    tw = TkinterWindow()

    tkinter_process = Process(target=tw.start)

    tkinter_process.start()
    flask_process.start()

    tkinter_process.join()
    c.execute('DROP TABLE temperatures')
    c.execute('DROP TABLE thresholds')
    conn.close()
