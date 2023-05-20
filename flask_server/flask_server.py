import random
import sqlite3
import tkinter as tk
from multiprocessing import Process, Manager

import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify


LOWER_THRESHOLD = 22
UPPER_THRESHOLD = 24


class TkinterWindow:
    ROOM_COLORS = ['green', 'blue', 'orange']

    def __init__(self, lower_threshold: int = LOWER_THRESHOLD, upper_threshold: int = UPPER_THRESHOLD):
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.connection, self.cursor = self._initialize_sqlite()

        self.window = tk.Tk()
        self.window.title("Temperature Monitor")

        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature')
        self.ax.set_title('Temperature Monitor')

        self.threshold_upper, = self.ax.plot([], [], 'r-', label='Upper Threshold')
        self.threshold_lower, = self.ax.plot([], [], 'b-', label='Lower Threshold')
        self.room_lines = [self.ax.plot([], [], '-',
                                        color=self.ROOM_COLORS[i],
                                        label='Room {}'.format(i + 1))[0]
                           for i in range(3)]
        self.lines = [self.threshold_upper, self.threshold_lower] + self.room_lines

        self.ax.legend()

        self.x_data = []
        self.y_data = [[] for _ in range(5)]

        self.manager = Manager()
        self.shared_data = self.manager.dict({'x_data': [], 'y_data': [[] for _ in range(5)]})

    def _initialize_sqlite(self):
        conn = sqlite3.connect('temperatures.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS temperatures
                     (time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, room INTEGER, temperature REAL)''')
        conn.commit()
        return conn, c

    def cleanup(self):
        self.connection.close()

    def update_plot(self):
        self.ax.clear()

        # Plot the threshold lines
        self.threshold_upper.set_data(self.shared_data['x_data'], [self.upper_threshold] * len(self.shared_data['x_data']))
        self.threshold_lower.set_data(self.shared_data['x_data'], [self.lower_threshold] * len(self.shared_data['x_data']))

        # Plot the room lines
        for i, line in enumerate(self.room_lines):
            line.set_data(self.shared_data['x_data'], self.shared_data['y_data'][i + 2])

        # Set plot limits
        self.ax.set_xlim(0, max(self.shared_data['x_data']) if self.shared_data['x_data'] else 1)
        self.ax.set_ylim(0, 30)  # Set appropriate y-axis limits based on your needs

        # Add labels and legend
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature')
        self.ax.set_title('Temperature Monitor')
        self.ax.legend()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def animate(self, frame):
        self.cursor.execute('''SELECT room, temperature FROM temperatures
                     ORDER BY time DESC
                     LIMIT 10''')
        rows = self.cursor.fetchall()
        if rows:
            for i, row in enumerate(rows):
                room, temperature = row
                self.y_data[i + 2].append(temperature)

        self.x_data.append(frame)

        self.update_plot(frame)

    def update_temperatures(self):
        for temp in TEMPERATURES:
            temp.change_temperature()
            self.cursor.execute("INSERT INTO temperatures(room, temperature) VALUES(?, ?)",
                                (temp.room, temp.current_temperature))
        self.connection.commit()
        self.animate(len(self.x_data))
        self.shared_data['x_data'] = self.x_data
        self.shared_data['y_data'] = self.y_data
        if len(self.x_data) > 1:
            plt.pause(1)  # Pause for 1 second before updating the plot again
            plt.show()

    def start(self):
        tkinter_process = Process(target=self.window.mainloop)
        animation_process = Process(target=self.animate, args=(0,))

        tkinter_process.start()
        animation_process.start()

        tkinter_process.join()

        animation_process.terminate()


class Temperature:
    def __init__(self, room):
        self.room = room
        self.current_temperature = random.randint(16, 20)
        self.is_heating = True
        self.change_rate = 0.1

    def change_temperature(self):
        if self.is_heating and self.current_temperature < UPPER_THRESHOLD:
            self.current_temperature = round(self.current_temperature + self.change_rate, 2)
        elif not self.is_heating and self.current_temperature >= LOWER_THRESHOLD:
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


def change_temperatures():
    for temp in TEMPERATURES:
        temp.change_temperature()


@app.route('/temperatures')
def get_temperatures():
    change_temperatures()
    conn = sqlite3.connect('temperatures.db')  # Create a new connection
    c = conn.cursor()
    insert_temperatures(c, TEMPERATURES)
    conn.commit()
    for temp in TEMPERATURES:
        print(f'Temperature in room {temp.room} is now {temp.current_temperature}')
    conn.close()
    return jsonify({'temperatures': [temp.current_temperature for temp in TEMPERATURES]})


@app.route('/toggle_light', methods=['POST'])
def toggle_light():
    data = request.get_json()
    light = data['light']
    print(f'Changing {light} in room {light.split("_")[1]} to state {not lights[light]}')
    lights[light] = not lights[light]
    return jsonify({'status': 'success'})


@staticmethod
def insert_temperatures(c, temperatures: list):
    for temperature in temperatures:
        c.execute("INSERT INTO temperatures(room, temperature) VALUES(?, ?)",
                  (temperature.room, temperature.current_temperature))


@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    data = request.json
    print(f'Setting brightness in room {data["brightness"]} to {data["value"]}')
    brightness[data['brightness']] = int(data['value'])
    return 'OK'


def start_flask():
    app.run(port=8080)


if __name__ == '__main__':
    flask_process = Process(target=start_flask)
    tw = TkinterWindow()

    tkinter_process = Process(target=tw.start)

    tkinter_process.start()
    flask_process.start()

    tkinter_process.join()

    conn.close()

