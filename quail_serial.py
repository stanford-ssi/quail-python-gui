#####################
'''
Module for talking to quail.  Sends and receives information.


Luke Upton
Feb 2020

'''
#####################

# Import Serial Interfacing Module
import serial
import time


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
        return measurements
            
    def write_command(self, command):
        command = int(command)
        print(command)
        self.serial.write((str(command) + '\r\n').encode())
        
        

