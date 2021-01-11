import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as dialog
from lib.QuailCommands import QuailCommands

INITIAL_PULSE_TIME = 1.0 # default starting pulse time
MAX_PULSE_TIME = 10 # maximum pulse time allowed, in seconds
MIN_PULSE_TIME = 0.1 # minimum pulse time allowed, in seconds

initial_commands = ["OxVent Pulse", "OxVent Hold", "OxFill Pulse", "OxFill Hold", "OxVent&Fill Pulse",
                    "OxVent&Fill Hold", "FuelPress Pulse", "FuelPress Hold", "Launch","ABORT"]  # default initial commands

class ButtonPane(ttk.Frame):
    def __init__(self, mainwindow, mainframe, quail):
        super().__init__(mainframe) # use parent constructor with mainframe as parent
        
        # Create QuailCommands object, which has all the user-defined commands
        self.quailcmds = QuailCommands(quail, mainwindow, pulse_sec = INITIAL_PULSE_TIME)

        # Create PulseTime button, allows user to determine the duration of a pulse
        self.pulse_sec = INITIAL_PULSE_TIME
        self.pulse_time = tk.StringVar()
        self.pulse_time.set("Pulse Time= " + str(INITIAL_PULSE_TIME) + " sec")
        self.pulse_button = ttk.Button(self, textvariable= self.pulse_time, command= self.update_pulse )
        self.pulse_button.grid(row=0, column=0, sticky = 'nsew')

        # Create command list, which holds the text variable of each button
        self.commands = []
        for i in range(len(initial_commands)):
            self.commands.append(tk.StringVar())
            self.commands[i].set(initial_commands[i])

        # Create buttons, adding them to the buttons list
        self.buttons = []
        for i in range(len(self.commands)):
            c = self.commands[i]
            my_func = self.quailcmds.get_defined_commands(c.get())
            if i != len(self.commands) - 1:
                self.buttons.append(ttk.Button( self, style = "White.TButton", textvariable = c))
                self.buttons[i].bind("<ButtonPress-1>", my_func)
            else: # Abort button is red and requires a double-click
                self.buttons.append(ttk.Button( self, style = "Red.TButton", textvariable=c))
                self.buttons[i].bind("<Double-Button-1>", my_func)
            self.buttons[i].grid(row= i+1, column = 0, sticky = 'nsew')   
            self.rowconfigure(i+1, weight=1) 
        self.columnconfigure(0,weight=1)
    
    def update_pulse(self):
        # Open a dialog, take user input, and update the button label appropriately, limiting with the MAX/MIN defined at top of file
        new_time = dialog.askfloat("Update Pulse Time", "New Pulse Time in Seconds: ")
        if new_time != None:
            new_time = max(MIN_PULSE_TIME, min(new_time, MAX_PULSE_TIME))
            self.pulse_time.set("Pulse Time = " + str(new_time) +" sec")
            self.pulse_sec = new_time
    
    def open_command_dialog(self):
        win = tk.Toplevel()
        win.grab_set()
        win.wm_title("Command Dialog")
        drops = []
        command_options = sorted(self.quailcmds.get_defined_commands())
        for i in range(len(self.commands)-1):
            l = tk.Label(win, text="Button #"+str(i+1))
            l.grid(row=i, column=0)
            var = tk.StringVar(win)
            var.set(self.commands[i].get())
            b = ttk.OptionMenu(win,var,self.commands[i].get(),'-',*command_options)
            b.grid(row=i,column=1,sticky='ew')
            drops.append(var)
        update = tk.Button(win,text = "Update Buttons",command = lambda: update_buttons(drops))
        update.grid(row = len(self.commands), column = 1)
        def update_buttons(drops):
            for i in range(len(self.commands)-1):
                d = drops[i].get()
                self.commands[i].set(d) # update stringvars with new button functions
                my_func = self.quailcmds.get_defined_commands(d)
                self.buttons[i].unbind("<ButtonPress-1>")
                self.buttons[i].bind("<ButtonPress-1>", my_func) #update buttons with new commands