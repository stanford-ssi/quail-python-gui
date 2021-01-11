#####################
'''
Module for talking to quail.  Sends and receives information.


Luke Upton + Max Newport
Oct 2020

'''
#####################

# Import Serial Interfacing Module
import serial
import time
import threading
import __main__
import numpy as np
import sys, os
from datetime import datetime

num_elements_in_tick = 1 + 6 + 1 # number of data elements in each stream ( zero check, num data channels, time)
record_to = None
data_f = None

# Create quail class that can be called as object later on
class quail:
    def __init__(self, COM_Port=11, baud_rate =115200):
        # Establish connection and print test data
        # self.serial = serial.Serial('COM{}'.format(COM_Port))
        self.COM_Port = COM_Port
        self.data = None
        # print(self.serial.readline())
        
    
    def get_measurements(self):
        # Clear device (laptop buffer)
        self.serial.reset_input_buffer()
        time.sleep(0.01)
        # Query device for string containing measurement values
        val_string = str(self.serial.readline())
        # Break the value string apart
        val_string = val_string.strip("\\n\\r,b'").split(',')
        # convert measurements to float and return
        measurements = []
        for val in val_string:
            measurements.append(float(val))
        measurements = np.asarray(measurements)
        if self.data == None :
            self.data = np.zeros((1, np.size(measurements)))
            self.data[0,:] = measurements
        elif measurements[0] == 0:
            np.append(self.data, measurements, axis = 0)

        if __main__.recording:
            if record_to == None:
                __main__.record_label.configure(text = "RECORDING",background = colors[0],foreground='white')
                now=datetime.now()
                d_string = now.strftime("%d_%m_%Y")
                t_string = now.strftime("%H_%M_%S")
                file_base = sys.path[0]
                add_on = "/Data/"+d_string
                if not os.path.exists(file_base+add_on):
                    try: 
                        os.makedirs(sys.path[0] + add_on)
                        file_base = file_base + add_on
                    except OSError:
                        pass
                else:
                    file_base = file_base + add_on
                record_to = file_base + "/" + test_name.get().split(":")[1].strip() + "___" + d_string + "___" + t_string + ".txt"
                data_f=open(record_to,'w+')
        elif data_f != None:
            __main__.record_label.configure(text = "Not Recording",background = 'white',foreground=colors[0])
            record_to = None
            data_f.close()

        return measurements[1:]
            
    def write_command(self, command):
        try: #handle simple numeric command
            command = int(command)
            print("Writing command: " + str(command))
            try:
                timer.sleep(0.05) #wait to ensure any command before this one has sent
                self.serial.write((str(command) + '\r\n').encode())
            except:
                print("Failure sending command to Quail...")

        except: #handle list of commands or equation with "wait##"
            try: # if user passed in a string, check if alias or equation and break into iterable list of numeric commands/waits
                if isinstance(command, str): # if item passed in is a string waiting to be broken up
                    command = command.strip().lower()
                    try:
                        for key in __main__.valid_quail_commands.keys():
                            if command == (key.split('\t')[0]).strip().lower() : # if command is an alias
                                self.write_command(__main__.valid_quail_commands[key])
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
                        timer = threading.Timer(c,lambda : self.write_command(commands[i+1:]))
                        timer.start() 
                    except:
                        pass # if the command fails after waiting or if wait was last command, pass to the return statement below
                    return # thread will start new function call with remaining commands after timer elapses, so can return here
                else:
                    c = int(c)
                    print("Writing command: " + str(c))
                    try:
                        time.sleep(.05) #wait to ensure previous command has sent
                        self.serial.write((str(command) + '\r\n').encode()) #convert unicode string to utf-8 and send through serial
                    except:
                        print("Failure sending command to Quail...")
                        return # if you fail to send a command in the string, don't try to send more
            
        
        

