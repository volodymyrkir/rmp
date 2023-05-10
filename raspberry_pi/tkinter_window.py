from tkinter import Tk, Label, Button, Entry, Scale, Listbox, Widget, IntVar
from tkinter import N, S, E, W, Scrollbar, HORIZONTAL, END

from datetime import datetime

from mqtt.mqtt_connector import MqttConnector


class TkinterWindow:
    counter_value = 0
    state = False
    threshold = None
    color_changed = False

    def __init__(self, window_width: int, window_length: int, counter_limit: int):
        self.tkinter_entity = Tk()
        self.tkinter_entity.title("Volodymyr Kiriushyn")
        self.tkinter_entity.geometry(f'{window_width}x{window_length}')

        self._cur_row_left = 1
        self._cur_row_right = 7
        self._actions = []
        self._counter_limit = counter_limit
        self._init_components()
        self.mqtt_connector = self._initialize_client()
        self.mqtt_connector.client_publish(str(self.counter_value))

    def _initialize_client(self):
        client = MqttConnector()
        client.subscribe_client(on_message=self._client_on_message)
        return client

    def _button_pressed(self):

        if self.counter_value + 1 <= self._counter_limit:
            self.counter_value += 1
            self.mqtt_connector.client_publish(str(self.counter_value))
            self._counter_label.config(text=f"Counter={self.counter_value}")
            event = f"At {datetime.now().time().strftime('%H:%M:%S')}" \
                    f" counter is changed by Button, new value is {self.counter_value}"
            self._list_box.insert(END, event)

        self._check_threshold()

        self.state = not self.state
        self._boolean_label.config(text=f"State is {self.state}")

    def _client_on_message(self, client, userdata, msg):
        value = int(msg.payload.decode())
        if value < self._counter_limit and (not self.threshold or self.threshold >= value):
            self.counter_value = value
            self._counter_label.config(text=f"Counter={self.counter_value}")
            self.slider_val.set(value)
            event = (f"At {datetime.now().time().strftime('%H:%M:%S')}"
                     f" counter is changed by mobile client,"
                     f" new value is {self.counter_value}")
            self._list_box.insert(END, event)

    def _threshold_entered(self, event):
        potential_threshold = self._threshold_entry.get()
        if not potential_threshold.isnumeric():
            raise ValueError("Wrong M value, go for integer")
        else:
            self.threshold = int(potential_threshold)
            self._check_threshold()

    def _check_threshold(self):
        if self.threshold:
            if self.counter_value >= self.threshold and not self.color_changed:
                self._counter_label.config(text=f"Counter={self.counter_value}", background='red')
            else:
                self._counter_label.config(text=f"Counter={self.counter_value}", bg='light gray')
        return

    def _process_slider_changes(self, value):
        self.counter_value = int(value)
        self._counter_label.config(text=f"Counter={self.counter_value}")
        event = f"At {datetime.now().time().strftime('%H:%M:%S')}" \
                f" counter is changed by Slider, new value is {self.counter_value}"
        self._list_box.insert(END, event)
        if self.threshold:
            self._check_threshold()

    def _init_components(self):

        self._counter_label = Label(self.tkinter_entity, text=f"Counter={self.counter_value}", font=('Bold', 15))

        self._increment_button = Button(self.tkinter_entity,
                                        text="Increment & reverse",
                                        command=self._button_pressed,
                                        font=('Bold', 15))

        self._boolean_label = Label(self.tkinter_entity, text=f"State is {self.state}", font=('Bold', 15))

        self._threshold_label = Label(self.tkinter_entity, text="Enter threshold (M)", font=('Bold', 15))

        self._threshold_entry = Entry(self.tkinter_entity, font=('Bold', 20), width=10)
        self._threshold_entry.bind("<Return>", self._threshold_entered)
        self._threshold_entry.focus_set()

        self.slider_val = IntVar()
        self._slider = Scale(self.tkinter_entity, from_=0, to=self._counter_limit,
                             command=self._process_slider_changes,variable=self.slider_val,
                             orient=HORIZONTAL,
                             tickinterval=4, resolution=1, length=450)

        self._list_box = Listbox(self.tkinter_entity, height=20, width=45, font=('Bold', 9))
        self._list_box.grid(column=1, row=1, rowspan=5, sticky=N + S + W + E)
        self._scrollbar = Scrollbar(self.tkinter_entity)
        self._scrollbar.grid(column=2, row=1, sticky=N + S)
        self._list_box.config(yscrollcommand=self._scrollbar.set)
        self._scrollbar.config(command=self._list_box.yview)

        self._add_widget_left(self._counter_label)
        self._add_widget_left(self._increment_button)
        self._add_widget_left(self._boolean_label)
        self._add_widget_left(self._threshold_label)
        self._add_widget_left(self._threshold_entry)
        self.tkinter_entity.columnconfigure(0, weight=1)
        self.tkinter_entity.columnconfigure(1, weight=1)
        self._slider.grid(columnspan=2, sticky='ew')

    def _add_widget_left(self, widget: Widget):
        widget.grid(row=self._cur_row_left, column=0, padx=10, pady=30)
        self._cur_row_left += 1

    def _add_widget_right(self, widget: Widget):
        widget.grid(row=self._cur_row_right, column=1, pady=10)
        self._cur_row_right += 1

    def run(self):
        self.tkinter_entity.mainloop()


if __name__ == "__main__":
    tkinter_app = TkinterWindow(640, 540, 64)
    tkinter_app.run()
