'''
RecordingPane:

The pane that owns the Test Name text entry to allow users to customize record-file names. Owns the record button.
Communicates with Quail via multiprocessing-safe queues.
'''

import tkinter as tk
import tkinter.ttk as ttk
import re

DEFAULT_TEST_NAME = "GUI_TEST"

class RecordingPane(ttk.Frame):
    def __init__(self, mainframe, quail):
        super().__init__(master=mainframe)
        
        self.quail = quail

        self.test_name = tk.StringVar()
        self.test_name.set(DEFAULT_TEST_NAME) #initial test name, can be updated during runtime
        self.testname_label = ttk.Label(self,text = "Test Name:")
        self.testname_label.grid(row = 0, column = 0, sticky= 'nsew')
        self.testname_entry = ttk.Entry(self, textvariable = self.test_name)
        self.testname_entry.grid(row = 0, column = 1, sticky = 'nsew')
        self.record_button_var = tk.StringVar()
        self.record_button_var.set("\u25B6 Start Recording")
        self.record_button = ttk.Button(self, textvariable = self.record_button_var, style = "White.TButton", command = self.start_recording)
        self.record_button.grid(row = 0, column = 2, sticky = 'nsew')

        self.rowconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)

    def start_recording(self):
        self.quail.start_recording(re.sub('\W+','',self.test_name.get().strip()) ) # pass filename, clearing special characters and punctuation (except underscore)
        self.testname_entry.configure(state = 'disabled')
        self.record_button_var.set("\u25A0 Stop Recording")
        self.record_button.configure(command = self.stop_recording, style = "Red.TButton")

    def stop_recording(self):
        self.quail.stop_recording()
        self.testname_entry.configure(state = 'enabled')
        self.record_button_var.set("\u25B6 Start Recording")
        self.record_button.configure(command = self.start_recording, style = "White.TButton")