import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox

from quail_serial import *

def get_defined_commands(command = ""):
    command_func = {
        "Launch" :  launch,
        "OxVent 1s" : oxvent1,
        "-" : lambda: None
    }
    if command == "":
        return list(command_func.keys())
    else:
        return command_func[command]


def launch():
    if msgbox.askokcancel ('Launch Confirmation','Initiate Launch Sequence?',icon = 'warning') : 
       msgbox.askokcancel('Uhhh you didnt write that command yet')
    pass

def oxvent1():
    global quail
    pulse_time = 1 # sec
    quail.write_command(11)
    timer = threading.Timer(pause_time, quail.write_command(12))
    timer.start() # pulses for 1 sec without blocking other updates


def open_command_dialog(curr_commands, buttons):
    win = tk.Toplevel()
    win.grab_set()
    win.wm_title("Command Dialog")
    drops = []
    command_options = get_defined_commands()
    for i in range(len(curr_commands)):
        l = tk.Label(win, text="Button #"+str(i+1))
        l.grid(row=i, column=0)
        var = tk.StringVar(win)
        var.set(curr_commands[i].get())
        b = ttk.OptionMenu(win,var,curr_commands[i].get(),'-',*command_options)
        b.grid(row=i,column=1)
        drops.append(var)
    update = tk.Button(win,text = "Update Buttons",command = lambda: update_buttons(drops, curr_commands))
    update.grid(row = len(curr_commands), column = 1)
    def update_buttons(drops, commands):
        for i in range(len(commands)):
            d = drops[i].get()
            commands[i].set(d) # update stringvars with new button functions
            buttons[i].configure(command=get_defined_commands(d)) #update buttons with new commands

    
    


