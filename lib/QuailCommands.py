'''
QuailCommands:

Class that owns user-defined commands to which buttons can be linked in the ButtonPane. 
'''

import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import tkinter.simpledialog as dialog


''' Quail command base values and channel indicators for command codes. '''
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

class QuailCommands:
    def __init__(self, quail, mainwindow, pulse_sec = 1.0):
        self.quail = quail
        self.mainwindow = mainwindow 
        self.pulse_sec = pulse_sec # Time duration in sec of pulse
        self.command_funcs = { # Library of command functions (will be passed an event on call)
            "ABORT" : lambda event: self.abort(),
            "Launch" :  lambda event: self.launch(),
            "OxVent Pulse" : lambda event: self.pulse_solenoids(oxvent_ch),
            "OxVent Hold" : lambda event: self.hold_solenoids(oxvent_ch),
            "FuelPress Pulse" : lambda event: self.pulse_solenoids(fuelpress_ch),
            "FuelPress Hold" : lambda event: self.hold_solenoids(fuelpress_ch),
            "OxFill Pulse" : lambda event: self.pulse_solenoids(oxfill_ch),
            "OxFill Hold" : lambda event: self.hold_solenoids(oxfill_ch),
            "OxVent&Fill Pulse" : lambda event: self.pulse_solenoids([oxfill_ch, oxvent_ch]),
            "OxVent&Fill Hold" : lambda event: self.hold_solenoids([oxfill_ch, oxvent_ch]),
            "OxAbort Pulse" : lambda event: self.pulse_solenoids(oxabort_ch),
            "OxAbort Hold" : lambda event: self.hold_solenoids(oxabort_ch),
            "FuelAbort Pulse" : lambda event: self.pulse_solenoids(fuelabort_ch),
            "FuelAbort Hold" : lambda event: self.hold_solenoids(fuelabort_ch),
            "ExtraSol Pulse" : lambda event: self.pulse_solenoids(extrasol_ch),
            "ExtraSol Hold" : lambda event: self.hold_solenoids(extrasol_ch),
            "Open Fuel Pyro" : lambda event: self.fire_squib(fuelpyro_ch),
            "Open Ox Pyro" : lambda event: self.fire_squib(fuelpyro_ch),
            "Start Igniter" : lambda event: self.fire_squib(igniter_ch),
            "Open BOTH Pyro" : lambda event: self.fire_squib([fuelpyro_ch, oxpyro_ch]),
            "-" : lambda event: None
        }

    def get_defined_commands(self, command = ""):
        ''' If passed a command, returns the event corresponding to that command. Otherwise, passes all 
            available commands. '''
        if command == "":
            return list(self.command_funcs.keys())
        else:
            return self.command_funcs[command]

    def launch(self):
        ''' Launch command that opens dialogs to confirm launch, then count down to ignition. '''
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
            self.mainwindow.unbind("<space>")
            if not cancelled:
                try:
                    secs.grid_remove()
                    count.grid_remove()
                except:
                    return # if these items no longer exist, thats a sign that the user closed the window
                tmin.configure(text = "LAUNCH SEQUENCE INITIATED",background = "#a83232", foreground = "white")
                self.quail.write_command(close_offset+oxfill_ch)
                self.quail.write_command(close_offset+fuelpress_ch)
                self.quail.write_command(open_offset+oxvent_ch)
                self.quail.write_command(launch_command)
            else:
                try:
                    win.destroy()
                    mainwindow.mainframe.focus()
                except:
                    pass
            
        if msgbox.askyesno('Launch Confirmation','Initiate Launch Sequence? (yes to begin countdown)',icon="warning"): 
            cancelled = False
            countdown = tk.IntVar()
            countdown.set(10)
            self.mainwindow.bind("<space>",lambda event: canc(cancelled))
            timer = threading.Timer(1, lambda: decrement(countdown, cancelled))
            timer.start()
            win = tk.Toplevel()
            win.grab_set()
            win.bind("<space>",lambda event: canc(cancelled))
            space = ttk.Label(win,text="Press <SPACE> at any time to cancel launch.")
            space.grid(row = 0, column = 0, columnspan = 3, sticky= 'nsew')
            tmin = ttk.Label(win,text=" T MINUS ", font = ('TkDefaultFont', 18, 'bold'))
            tmin.grid(row = 1, column = 0, sticky= 'nsew')
            secs = ttk.Label(win,text=" SECONDS UNTIL IGNITION",font = ('TkDefaultFont', 18, 'bold'))
            secs.grid(row = 1, column = 2, sticky= 'nsew')
            count = ttk.Label(win,font = ('TkDefaultFont', 18, 'bold'), textvariable=countdown, background = "#a83232", foreground = "white")
            count.grid(row = 1, column = 1, sticky= 'nsew')
            win.columnconfigure(0,weight =1)
            win.columnconfigure(1,weight =1)
            win.columnconfigure(2,weight =1)
            win.rowconfigure(0,weight =1)
            win.rowconfigure(1,weight =1)

    def abort(self):
        ''' Command for aborting - fires closes fill/press lines, opens ox vent, and blows fuel pyrovalve. '''
        self.quail.write_command(close_offset+oxfill_ch)  #close ox fill
        self.quail.write_command(close_offset+fuelpress_ch) #close fuel press
        self.quail.write_command(open_offset+oxvent_ch)  #open ox vent
        self.quail.write_command(fuelpyro_ch + squib_offset) # fire fuel pyrovalve

    def pulse_solenoids(self, solenoid_base):
        ''' Pulses the solenoid determined by solenoid_base. '''
        def close_sol(): # command to which thread returns after waiting "pulse_sec"
            for base in solenoid_base:
                self.quail.write_command(base+close_offset)
        try:
            solenoid_base[0]
        except TypeError:
            solenoid_base = [solenoid_base] #make sure base is iterable - if single, wrap in brackets
        for base in solenoid_base:
            self.quail.write_command(base + open_offset)
        timer = threading.Timer(self.pulse_sec, close_sol)
        timer.start() # pulses for pulse_sec without blocking other updates by starting parallel thread

    def hold_solenoids(self, solenoid_base):
        ''' Holds a solenoid open until the user stops clicking. '''
        def close_on_release(): # command to call when button released
            for base in solenoid_base: # if mouse released, close solenoids
                self.quail.write_command(base + close_offset)
            self.mainwindow.unbind("<ButtonRelease-1>")
        try:
            solenoid_base[0]
        except TypeError:
            solenoid_base = [solenoid_base] #make sure base is iterable - if single, wrap in brackets
        for base in solenoid_base:
            self.quail.write_command(base + open_offset)
        self.mainwindow.bind("<ButtonRelease-1>",lambda event: close_on_release())

    def fire_squib(self, squib_base):
        ''' Fires the squib determined by squib_base. '''
        try:
            squib_base[0]
        except TypeError:
            squib_base = [squib_base] #make sure base is iterable - if single, wrap in brackets
        for base in squib_base:
            self.quail.write_command(base + squib_offset)