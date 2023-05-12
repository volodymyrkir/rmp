import random

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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


def generate_temperatures():
    temperatures = [random.randint(15, 23   ) for _ in range(3)]
    return temperatures


@app.route('/temperatures')
def get_temperatures():
    temperatures = generate_temperatures()
    for room in range(3):
        print(f'Temperature in room {room+1} is now {temperatures[room]}')
    return jsonify({'temperatures': generate_temperatures()})


@app.route('/toggle_light', methods=['POST'])
def toggle_light():
    data = request.get_json()
    light = data['light']
    print(f'Changing {light} in room {light.split("_")[1]} to state {not lights[light]}')
    lights[light] = not lights[light]
    return jsonify({'status': 'success'})


@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    data = request.json
    print(f'Setting brightness in room {data["brightness"]} to {data["value"]}')
    brightness[data['brightness']] = int(data['value'])
    return 'OK'


if __name__ == '__main__':
    app.run(port=8080)
