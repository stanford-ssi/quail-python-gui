import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import tkinter.simpledialog as dialog
import __main__ 
from quail_serial import *

pulse_sec = 1.0
open_offset = 10 # open command is 10 + solenoid number
close_offset = 20 # close command is 20 + solenoid number
squib_offset = 60 # squib command is 60 + squib channel
oxvent_ch = 1
fuelpress_ch = 2
oxfill_ch = 3
oxabort_ch = 4
fuelabort_ch = 5
extrasol_ch = 6
fuelpyro_ch = 1
oxpyro_ch = 5
igniter_ch = 2
launch_command = 69 #launch command in quail, fires igniter, delays, then fires pyro valves simultaneously

def get_defined_commands(command = ""):
    command_func = {
        "ABORT" : abort,
        "Launch" :  launch,
        "OxVent Pulse" : lambda event: pulse_solenoids(oxvent_ch),
        "OxVent Hold" : lambda event: hold_solenoids(oxvent_ch),
        "FuelPress Pulse" : lambda event: pulse_solenoids(fuelpress_ch),
        "FuelPress Hold" : lambda event: hold_solenoids(fuelpress_ch),
        "OxFill Pulse" : lambda event: pulse_solenoids(oxfill_ch),
        "OxFill Hold" : lambda event: hold_solenoids(oxfill_ch),
        "OxVent&Fill Pulse" : lambda event: pulse_solenoids([oxfill_ch, oxvent_ch]),
        "OxVent&Fill Hold" : lambda event: hold_solenoids([oxfill_ch, oxvent_ch]),
        "OxAbort Pulse" : lambda event: pulse_solenoids(oxabort_ch),
        "OxAbort Hold" : lambda event: hold_solenoids(oxabort_ch),
        "FuelAbort Pulse" : lambda event: pulse_solenoids(fuelabort_ch),
        "FuelAbort Hold" : lambda event: hold_solenoids(fuelabort_ch),
        "ExtraSol Pulse" : lambda event: pulse_solenoids(extrasol_ch),
        "ExtraSol Hold" : lambda event: hold_solenoids(extrasol_ch),
        "Open Fuel Pyro" : lambda event: fire_squib(fuelpyro_ch),
        "Open Ox Pyro" : lambda event: fire_squib(fuelpyro_ch),
        "Start Igniter" : lambda event: fire_squib(igniter_ch),
        "Open BOTH Pyro" : lambda event: fire_squib([fuelpyro_ch, oxpyro_ch]),
        "-" : lambda event: None
    }
    if command == "":
        return list(command_func.keys())
    else:
        return command_func[command]

############################# BUTTON COMMAND OPTIONS ####################################

def launch(event):
    def canc(cancelled):
        cancelled = True
        countdown.set(-1)
        decrement(countdown, cancelled)
    def decrement(countdown, cancelled):
        if countdown.get() > 0 and not cancelled:
            try:
                countdown.set(countdown.get()-1)
                timer = threading.Timer(1, lambda: decrement(countdown, cancelled))
                timer.start()
            except:
                cancelled = True
                launch_now(cancelled)
        else:
            launch_now(cancelled)
    def launch_now(cancelled):
        __main__.root.unbind("<space>")
        if not cancelled:
            try:
                secs.grid_remove()
                count.grid_remove()
            except:
                return # if these items no longer exist, thats a sign that the user closed the window
            tmin.configure(text = "LAUNCH SEQUENCE INITIATED",background = __main__.colors[0], foreground = "white")
            __main__.quail.write_command(close_offset+oxfill_ch)
            __main__.quail.write_command(close_offset+fuelpress_ch)
            __main__.quail.write_command(open_offset+oxvent_ch)
            __main__.quail.write_command(launch_command)
        else:
            try:
                win.destroy()
            except:
                pass
        
    if msgbox.askyesno('Launch Confirmation','Initiate Launch Sequence? (yes to begin countdown)',icon="warning"): 
        cancelled = False
        countdown = tk.IntVar()
        countdown.set(10)
        __main__.root.bind("<space>",lambda event: canc(cancelled))
        timer = threading.Timer(1, lambda: decrement(countdown, cancelled))
        timer.start()
        win = tk.Toplevel()
        win.bind("<space>",lambda event: canc(cancelled))
        space = ttk.Label(win,text="Press <SPACE> at any time to cancel launch.")
        space.grid(row = 0, column = 0, columnspan = 3, sticky= 'nsew')
        tmin = ttk.Label(win,text=" T MINUS ", font = ('TkDefaultFont', 18, 'bold'))
        tmin.grid(row = 1, column = 0, sticky= 'nsew')
        secs = ttk.Label(win,text=" SECONDS UNTIL IGNITION",font = ('TkDefaultFont', 18, 'bold'))
        secs.grid(row = 1, column = 2, sticky= 'nsew')
        count = ttk.Label(win,font = ('TkDefaultFont', 18, 'bold'), textvariable=countdown, background = __main__.colors[0], foreground = "white")
        count.grid(row = 1, column = 1, sticky= 'nsew')
        win.columnconfigure(0,weight =1)
        win.columnconfigure(1,weight =1)
        win.columnconfigure(2,weight =1)
        win.rowconfigure(0,weight =1)
        win.rowconfigure(1,weight =1)

def abort(event):
    __main__.quail.write_command(close_offset+oxfill_ch)  #close ox fill
    __main__.quail.write_command(close_offset+fuelpress_ch) #close fuel press
    __main__.quail.write_command(open_offset+oxvent_ch)  #open ox vent
    __main__.quail.write_command(fuelpyro_ch + squib_offset) # fire fuel pyrovalve

def pulse_solenoids(solenoid_base):
    def close_sol(): # command to which thread returns after waiting "pulse_sec"
        for base in solenoid_base:
            __main__.quail.write_command(base+close_offset)
    try:
        solenoid_base[0]
    except TypeError:
        solenoid_base = [solenoid_base] #make sure base is iterable - if single, wrap in brackets
    for base in solenoid_base:
        __main__.quail.write_command(base + open_offset)
    timer = threading.Timer(pulse_sec, close_sol)
    timer.start() # pulses for pulse_sec without blocking other updates by starting parallel thread

def hold_solenoids(solenoid_base):
    def close_on_release(): # command to call when button released
        for base in solenoid_base: # if mouse released, close solenoids
            __main__.quail.write_command(base + close_offset)
        __main__.root.unbind("<ButtonRelease-1>")
    try:
        solenoid_base[0]
    except TypeError:
        solenoid_base = [solenoid_base] #make sure base is iterable - if single, wrap in brackets
    for base in solenoid_base:
        __main__.quail.write_command(base + open_offset)
    __main__.root.bind("<ButtonRelease-1>",lambda event: close_on_release())

def fire_squib(squib_base):
    try:
        squib_base[0]
    except TypeError:
        squib_base = [squib_base] #make sure base is iterable - if single, wrap in brackets
    for base in squib_base:
        __main__.quail.write_command(base + squib_offset)

######################## GUI FUNCTIONS FOR UPDATING VALUES ###############################

def update_pulse(pulse_time):
    global pulse_sec
    new_time = dialog.askfloat("Update Pulse Time", "New Pulse Time in Seconds: ")
    if new_time != None:
        pulse_time.set("Pulse Time = " + str(new_time) +" sec")
        pulse_sec = new_time

def open_command_dialog(curr_commands, buttons):
    win = tk.Toplevel()
    win.grab_set()
    win.wm_title("Command Dialog")
    drops = []
    command_options = sorted(get_defined_commands())
    for i in range(len(curr_commands)-1):
        l = tk.Label(win, text="Button #"+str(i+1))
        l.grid(row=i, column=0)
        var = tk.StringVar(win)
        var.set(curr_commands[i].get())
        b = ttk.OptionMenu(win,var,curr_commands[i].get(),'-',*command_options)
        b.grid(row=i,column=1,sticky='ew')
        drops.append(var)
    update = tk.Button(win,text = "Update Buttons",command = lambda: update_buttons(drops, curr_commands))
    update.grid(row = len(curr_commands), column = 1)
    def update_buttons(drops, commands):
        for i in range(len(commands)-1):
            d = drops[i].get()
            commands[i].set(d) # update stringvars with new button functions
            my_func = get_defined_commands(d)
            buttons[i].unbind("<ButtonPress-1>")
            buttons[i].bind("<ButtonPress-1>", my_func) #update buttons with new commands

    
