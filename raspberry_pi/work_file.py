from RPi import GPIO
# from RPi.GPIO import *
from tkinter import *


class Detector:

    def __init__(self, pin_in, pin_out, pin_PWM):

        self.window = Tk()

        self.window.title = "kiriushyn"
        self.window.geometry("500x400")

        self.bth_color = True
        self.btn = Button(self.window, text="LED", command=self.__turn_on_the_led, width=25, height=5, bg="red")
        self.btn.place(relx=0.5, rely=0.1, anchor=CENTER)

        self.scale_value = 0
        self.scale = Scale(self.window, orient=HORIZONTAL, length=300, from_=0, to=100, tickinterval=10, resolution=5)
        self.scale.place(relx=0.5, rely=0.25, anchor=CENTER)
        self.scale.bind("<ButtonRelease-1>", self.change_scale)

        self.movement_sensor = Label(self.window, text="Motion Sensor", bg='red')
        self.movement_sensor.place(relx=0.5, rely=0.55, anchor=CENTER)

        self.pin_in = pin_in
        self.pin_out = pin_out
        self.pin_PWM = pin_PWM
        self.is_light_on = False
        self.brightness = 100
        self.is_moving = False

    def start(self):
        print('init gpio')
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_in, GPIO.IN)
        GPIO.setup(self.pin_out, GPIO.OUT)
        GPIO.setup(self.pin_PWM, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin_PWM, 50)
        GPIO.add_event_detect(self.pin_in, GPIO.BOTH, callback=self.set_moving)
        self.pwm.start(100)

    def turn(self):  # ok
        self.is_light_on = not self.is_light_on
        if self.is_light_on:
            print('start')
            GPIO.output(self.pin_out, GPIO.HIGH)
        else:
            print('stop')
            GPIO.output(self.pin_out, GPIO.LOW)

    def set_brightness(self, value):  # ok
        if 0 <= value <= 100:
            self.brightness = value
            self.pwm.ChangeDutyCycle(self.brightness)

    def set_moving(self, event):  # ok
        self.is_moving = True if GPIO.input(self.pin_in) == 1 else False
        if self.is_moving:
            self.start_flashing()
        else:
            self.stop_flashing()

    def start_flashing(self):  # ok
        self.change_motion_sensor(True)
        print('start flashing')

    def stop_flashing(self):  # ok
        self.change_motion_sensor(False)
        print('stop flashing')

    def __turn_on_the_led(self):  # ok
        if self.bth_color is True:
            self.btn['bg'] = "green"
        else:
            self.btn['bg'] = "red"
        self.bth_color = not self.bth_color
        self.turn()

    def change_scale(self, event):  # ok
        self.scale_value = self.scale.get()
        self.set_brightness(self.scale_value)
        print(self.scale_value)

    def change_motion_sensor(self, status):  # ok
        if status is True:
            self.motion_sensor['bg'] = "green"
        else:
            self.motion_sensor['bg'] = "red"
