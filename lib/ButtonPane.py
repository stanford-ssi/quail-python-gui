import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as dialog
from lib.QuailCommands import QuailCommands

INITIAL_PULSE_TIME = 1.0 # default starting pulse time
MAX_PULSE_TIME = 10 # maximum pulse time allowed, in seconds
MIN_PULSE_TIME = 0.1 # minimum pulse time allowed, in seconds

initial_fuel_commands = ["FuelPress Pulse", "FuelPress Hold", "FuelBleed Hold", "-", "-", "-", "-",
                         "Launch","Abort Fuel", "ABORT (dbl-clk)"]  # default initial commands
initial_ox_commands = ["OxVent Pulse", "OxVent Hold", "OxFill Pulse", "OxFill Hold", "OxVent&Fill Pulse",
                    "OxVent&Fill Hold", "OxBleed Hold", "-", "Abort Ox","ABORT (dbl-clk)"]  # default initial commands
page_titles = ["Fuel Commands", "Ox Commands"]

class ButtonPane(ttk.Frame):
    def __init__(self, mainwindow, mainframe, quail):
        super().__init__(mainframe) # use parent constructor with mainframe as parent
        
        # Create QuailCommands object, which has all the user-defined commands
        self.quailcmds = QuailCommands(quail, mainwindow, self)

        # Create PulseTime button, allows user to determine the duration of a pulse
        self.pulse_sec = INITIAL_PULSE_TIME
        self.pulse_time = tk.StringVar()
        self.pulse_time.set("Pulse Time= " + str(INITIAL_PULSE_TIME) + " sec")
        self.pulse_button = ttk.Button(self, textvariable= self.pulse_time, command= self.update_pulse )
        self.pulse_button.grid(row=0, column=0, sticky = 'nsew')

        # Create SwitchPage button, allows user to switch to other button page
        self.on_first_page = True
        self.switchpage_button = ttk.Button(self, text = "Switch to "+page_titles[1], command = self.switch_pages)
        self.switchpage_button.grid(row=1, column=0, sticky = 'nsew')

        # Create separator to move the small buttons away from the command buttons
        separator = ttk.Separator(self, orient = 'horizontal')
        separator.grid(row = 2, column=0, sticky = 'nsew', pady = (0,10))

        # Create command list, which holds the text variable of each button
        self.fuel_commands = []
        for i in range(len(initial_fuel_commands)):
            self.fuel_commands.append(tk.StringVar())
            self.fuel_commands[i].set(initial_fuel_commands[i])

        self.ox_commands = []
        for i in range(len(initial_ox_commands)):
            self.ox_commands.append(tk.StringVar())
            self.ox_commands[i].set(initial_ox_commands[i])

        # Create buttons, adding them to the buttons list (initially on the fuel button page)
        self.buttons = []
        for i in range(len(self.fuel_commands)):
            c = self.fuel_commands[i]
            if i != len(self.fuel_commands) - 1:
                my_func = self.quailcmds.get_defined_commands(c.get())
                self.buttons.append(ttk.Button( self, style = "White.TButton", textvariable = c))
                self.buttons[i].bind("<ButtonPress-1>", my_func)
            else: # Abort button is red and requires a double-click
                my_func = self.quailcmds.get_defined_commands('ABORT')
                self.buttons.append(ttk.Button( self, style = "Red.TButton", textvariable=c))
                self.buttons[i].bind("<Double-Button-1>", my_func)
            self.buttons[i].grid(row= i+3, column = 0, sticky = 'nsew')   
            self.rowconfigure(i+3, weight=1) 
        self.columnconfigure(0,weight=1)
    
    def update_pulse(self):
        # Open a dialog, take user input, and update the button label appropriately, limiting with the MAX/MIN defined at top of file
        new_time = dialog.askfloat("Update Pulse Time", "New Pulse Time in Seconds: ")
        if new_time != None:
            new_time = max(MIN_PULSE_TIME, min(new_time, MAX_PULSE_TIME))
            self.pulse_time.set("Pulse Time = " + str(new_time) +" sec")
            self.pulse_sec = new_time

    def switch_pages(self):
        ''' Switches between the two button pages. '''
        self.on_first_page = not(self.on_first_page)
        if self.on_first_page:
            self.switchpage_button.configure(text =  "Switch to "+page_titles[1])
            new_commands = self.fuel_commands
        else:
            self.switchpage_button.configure(text =  "Switch to "+page_titles[0])
            new_commands = self.ox_commands

        for i in range(len(new_commands)-1):
            self.buttons[i].configure(textvariable = new_commands[i])
            my_func = self.quailcmds.get_defined_commands(new_commands[i].get())
            self.buttons[i].unbind("<ButtonPress-1>")
            self.buttons[i].bind("<ButtonPress-1>", my_func) #update buttons with new commands
    
    def open_command_dialog(self):
        win = tk.Toplevel()
        win.grab_set()
        win.wm_title("Command Dialog")
        fuel_drops = []
        ox_drops = []
        command_options = sorted(self.quailcmds.get_defined_commands())
        fuel_label = tk.Label(win, text="Fuel Commands")
        fuel_label.grid(row = 0, column = 1, sticky = 'nsew')
        ox_label = tk.Label(win, text="Ox Commands")
        ox_label.grid(row = 0, column = 2, sticky = 'nsew')
        for i in range(len(self.fuel_commands)-1):
            l = tk.Label(win, text="Button #"+str(i+1))
            l.grid(row=i+1, column=0)
            var = tk.StringVar(win)
            var.set(self.fuel_commands[i].get())
            b = ttk.OptionMenu(win,var,self.fuel_commands[i].get(),'-',*command_options)
            b.grid(row=i+1,column=1,sticky='ew')
            fuel_drops.append(var)
        for i in range(len(self.ox_commands)-1):
            var = tk.StringVar(win)
            var.set(self.ox_commands[i].get())
            b = ttk.OptionMenu(win,var,self.ox_commands[i].get(),'-',*command_options)
            b.grid(row=i+1,column=2,sticky='ew')
            ox_drops.append(var)
        update = tk.Button(win,text = "Update Buttons",command = lambda: update_buttons(fuel_drops, ox_drops))
        update.grid(row = len(self.fuel_commands), column = 1, columnspan = 2, sticky = 'nsew')
        def update_buttons(fuel_drops, ox_drops):
            for i in range(len(self.fuel_commands)-1):
                d = fuel_drops[i].get()
                self.fuel_commands[i].set(d) # update stringvars with new button functions
                if self.on_first_page:
                    my_func = self.quailcmds.get_defined_commands(d)
                    self.buttons[i].unbind("<ButtonPress-1>")
                    self.buttons[i].bind("<ButtonPress-1>", my_func) #update buttons with new commands
            for i in range(len(self.ox_commands)-1):
                d = ox_drops[i].get()
                self.ox_commands[i].set(d) # update stringvars with new button functions
                if not self.on_first_page:
                    my_func = self.quailcmds.get_defined_commands(d)
                    self.buttons[i].unbind("<ButtonPress-1>")
                    self.buttons[i].bind("<ButtonPress-1>", my_func) #update buttons with new commands
