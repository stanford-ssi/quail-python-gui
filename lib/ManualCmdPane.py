import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as dialog
import threading
import csv

commands_file = "Quail_Command_Defs.csv"

class ManualCmdPane(ttk.Frame):
    def __init__(self, mainwindow, mainframe, quail):
        super().__init__(master = mainframe)
        self.quail = quail

        self.valid_quail_commands = self.get_quail_commands(commands_file)

        self.command_write = tk.StringVar() #variable storing the command user wants to write to Quail
        self.command_selected = tk.StringVar()
        self.label_current_command = ttk.Label(self, textvariable=mainwindow.graphpanes.last_command, background = "#a83232", foreground = "white")
        self.label_command = ttk.Label(self, text = "Cur. Cmd:")
        self.entry_command = ttk.Entry(self, width = 7, textvariable=self.command_write)
        self.button_write = ttk.Button(self, text = "Write (Double-Click)")
        self.button_write.bind("<Double-Button-1>", lambda event: self.process_command(self.command_write.get()))
        self.command_drop_down = ttk.OptionMenu(self, self.command_selected, "-", *sorted(self.valid_quail_commands.keys()),command = self.update_curr_command )
        self.label_current_command.grid(row=0, column=1, columnspan=1, sticky = 'nsew')
        self.label_command.grid(row=0, column=0, columnspan=1, sticky = 'nsew')
        self.entry_command.grid(row=1, column=0, columnspan=2, sticky = 'nsew')
        self.button_write.grid(row=2, column=0, columnspan=2, sticky = 'nsew')
        self.command_drop_down.grid(row=3, column=0, columnspan=2, sticky = 'nsew')
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)
        self.grid_propagate(False)

    def add_alias(self):
        new_alias = dialog.askstring("Add/Replace Quail Command Alias", "Format: <Alias_Name> = <Command1> + wait<wait_val_seconds> + <Command2> + ...")
        new_alias = new_alias.split("=")
        self.valid_quail_commands[new_alias[0]+"\t"+new_alias[1]] = new_alias[1]
        menu = self.command_drop_down["menu"]
        menu.delete(0, 'end')
        for key in sorted(self.valid_quail_commands.keys()):
            key = key.strip()
            menu.add_command(label = key, command = lambda v=key: self.update_curr_command(v))

    def update_curr_command(self, value):
        self.command_write.set(self.valid_quail_commands[value])
        self.command_selected.set("-")

    def process_command(self, command):
        try: #handle simple numeric command
            command = int(command)
            self.quail.write_command(command)
            
        except: #handle list of commands or equation with "wait##"
            try: # if user passed in a string, check if alias or equation and break into iterable list of numeric commands/waits
                if isinstance(command, str): # if item passed in is a string waiting to be broken up
                    command = command.strip().lower()
                    try:
                        for key in self.valid_quail_commands.keys():
                            if command == (key.split('\t')[0]).strip().lower() : # if command is an alias
                                self.write_command(self.valid_quail_commands[key])
                                return
                    except:
                        pass
                    commands = command.split('+') #try to split into individual functions separated by +
                else: # if not a string, must be a list of numeric commands/waits
                    commands = command[:] # if not a string, must be iterable of strings/ints

            except: #if cant break into an iterable, throw error
                print("INVALID COMMAND : " + str(command))
                return
            
            # Validate entire string of commands before attempting to run any one
            for i in range(len(commands)):
                c = commands[i].strip()
                try:
                    if c[:4] == "wait": #if a wait command, make sure what follows is numeric wait value
                        c = c[4:].strip()
                        c = float(c)
                    else: # if not a wait command, must be a numeric command
                        c = int(c)
                except:
                    print("INVALID COMMAND ENCOUNTERED : " + str(command))
                    return

            # Call functions if iterable list was valid
            for i in range(len(commands)):
                c = commands[i].strip()
                if c[:4] == "wait" :
                    c = c[4:].strip() # strip wait indicator off and start timer thread
                    c = float(c)
                    try: # handles case where timer is last item in command string, just skips
                        timer = threading.Timer(c,lambda : self.process_command(commands[i+1:]))
                        timer.start() 
                    except:
                        pass # if the command fails after waiting or if wait was last command, pass to the return statement below
                    return # thread will start new function call with remaining commands after timer elapses, so can return here
                else:
                    c = int(c)
                    self.quail.write_command(c)

    def get_quail_commands(self, filename):
        valid_quail_commands = {"-":0}
        with open(filename, newline="") as csvfile:
            myreader = csv.reader(csvfile, delimiter=',')
            for row in myreader:
                try:
                    valid_quail_commands[row[1].strip() +"\t" + row[0].strip()] = row[0]
                except: 
                    pass
        return valid_quail_commands