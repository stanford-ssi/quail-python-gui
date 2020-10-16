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


# Create quail class that can be called as object later on
class quail:
    def __init__(self, COM_Port=11, baud_rate =115200):
        # Establish connection and print test data
        self.serial = serial.Serial('COM{}'.format(COM_Port))
        self.COM_Port = COM_Port
        print(self.serial.readline())

    
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
        if measurements[0] != 0:
            return None # zero check first item in measurement
        return measurements[1:]
            
    def write_command(self, command):
        try: #handle simple numeric command
            command = int(command)
            print("Writing command: " + str(command))
            self.serial.write((str(command) + '\r\n').encode())
        except: #handle list of commands or equation with "wait15.5"
            try:
                if isinstance(command, str): # if item passed in is a string waiting to be broken up
                    commands = command.split('+') #try to split into individual functions separated by +
                else:
                    commands = command[:] # if not a string, must be iterable of strings/ints
            except:
                print("INVALID COMMAND : " + str(command))
                return
            
            # Validate string of commands before attempting to run
            for i in range(len(commands)):
                c = commands[i]
                try:
                    if c[:4] == "wait":
                        c = c[4:].strip()
                        c = float(c)
                    else:
                        c = int(c)
                except:
                    print("INVALID COMMAND ENCOUNTERED : " + str(command))
                    return

            # Call functions if valid
            for i in range(len(commands)):
                c = commands[i]
                if c[:4] == "wait" :
                    c = c[4:].strip() # strip wait indicator off and start timer thread
                    c = float(c)
                    try: # handles case where timer is last item in command string, just skips
                        timer = threading.Timer(c,lambda : self.write_command(commands[i+1:]))
                        timer.start() 
                    except:
                        pass
                    return # return function, as thread will start new function call with remaining commands after timer elapses
                else:
                    c = int(c)
                    time.sleep(.05) #wait to ensure previous command has sent
                    print("Write command: " + str(c))
                    self.serial.write((str(command) + '\r\n').encode())
            
        
        

