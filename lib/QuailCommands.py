'''
QuailCommands:

Class that owns user-defined commands to which buttons can be linked in the ButtonPane. 
'''

import threading
import time
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
oxbleed_ch = 4
fuelbleed_ch = 5
extrasol_ch = 6
fuelpyro_ch = 1
oxpyro_ch = 5
igniter_ch = 2
launch_command = 69 #launch command in quail, fires igniter, delays, then fires pyro valves simultaneously

class QuailCommands:
    def __init__(self, quail, mainwindow, parent):
        self.quail = quail
        self.mainwindow = mainwindow 
        self.parent = parent
        self.command_funcs = { # Library of command functions (will be passed an event on call)
            "ABORT" : lambda event: self.abort(),
            "Abort Ox" : lambda event: self.abort_ox(),
            "Abort Fuel" : lambda event: self.abort_fuel(),
            "Launch" :  lambda event: self.launch(),
            "OxVent Pulse" : lambda event: self.pulse_solenoids(oxvent_ch),
            "OxVent Hold" : lambda event: self.hold_solenoids(oxvent_ch),
            "FuelPress Pulse" : lambda event: self.pulse_solenoids(fuelpress_ch),
            "FuelPress Hold" : lambda event: self.hold_solenoids(fuelpress_ch),
            "OxFill Pulse" : lambda event: self.pulse_solenoids(oxfill_ch),
            "OxFill Hold" : lambda event: self.hold_solenoids(oxfill_ch),
            "OxVent&Fill Pulse" : lambda event: self.pulse_solenoids([oxfill_ch, oxvent_ch]),
            "OxVent&Fill Hold" : lambda event: self.hold_solenoids([oxfill_ch, oxvent_ch]),
            "OxBleed Pulse" : lambda event: self.pulse_solenoids(oxbleed_ch),
            "OxBleed Hold" : lambda event: self.hold_solenoids(oxbleed_ch),
            "FuelBleed Pulse" : lambda event: self.pulse_solenoids(fuelbleed_ch),
            "FuelBleed Hold" : lambda event: self.hold_solenoids(fuelbleed_ch),
            "ExtraSol Pulse" : lambda event: self.pulse_solenoids(extrasol_ch),
            "ExtraSol Hold" : lambda event: self.hold_solenoids(extrasol_ch),
            "Open Fuel Pyro" : lambda event: self.fire_squib(fuelpyro_ch),
            "Open Ox Pyro" : lambda event: self.fire_squib(fuelpyro_ch),
            "Open Bleeds" : lambda event: self.open_bleeds(),
            "Close Bleeds" : lambda event: self.close_bleeds(),
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
        ''' Launch command that opens dialogs to confirm launch, then starts launch sequence. '''          
        response = dialog.askfloat('Launch Confirmation','Enter any number and press OK to start launch sequence.\n (Closes fill/press/vent and immediately sends launch command)')
        try:    
            response = int(response)
            self.quail.write_command(close_offset+oxfill_ch)
            self.quail.write_command(close_offset+fuelpress_ch)
            self.quail.write_command(close_offset+oxvent_ch)
            self.quail.write_command(launch_command)
        except:
            return
            

    def abort(self):
        ''' Command for aborting - fires closes fill/press lines, opens ox vent, and blows fuel pyrovalve. '''
        self.quail.write_command(close_offset+oxfill_ch)  #close ox fill
        self.quail.write_command(close_offset+fuelpress_ch) #close fuel press
        self.quail.write_command(open_offset+oxvent_ch)  #open ox vent
        self.quail.write_command(fuelpyro_ch + squib_offset) # fire fuel pyrovalve
    
    def abort_ox(self):
        ''' Command for aborting ox side only - fires closes fill line, opens ox vent. '''
        self.quail.write_command(close_offset+oxfill_ch)  #close ox fill
        self.quail.write_command(open_offset+oxvent_ch)  #open ox vent
    
    def abort_fuel(self):
        ''' Command for aborting fuel side only - fires closes press line and blows fuel pyrovalve. '''
        self.quail.write_command(close_offset+fuelpress_ch) #close fuel press
        self.quail.write_command(fuelpyro_ch + squib_offset) # fire fuel pyrovalve

    def open_bleeds(self):
        ''' Opens both bleed solenoids - does not send any close command. '''
        self.quail.write_command(open_offset + fuelbleed_ch)
        self.quail.write_command(open_offset + oxbleed_ch)
    
    def close_bleeds(self):
        ''' Closes both bleed solenoids. '''
        self.quail.write_command(close_offset + fuelbleed_ch)
        self.quail.write_command(close_offset + oxbleed_ch)

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
        timer = threading.Timer(self.parent.pulse_sec, close_sol)
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