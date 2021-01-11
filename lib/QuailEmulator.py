'''
QuailEmulator:

A very simple serial emulator that feeds data in a method similar to Quail. Data is pulled from a csv file,
and the readline command waits until each data line's indicated time has passed before passing it to the function.

Includes the ability to time out and write commands.
'''

import numpy as np
import time
import linecache

READFILE = 'lib/QuailEmulator_data.csv' # this file contains 

class QuailEmulator:
    def __init__(self, COM_Port, timeout = -1):
        self.timeout = timeout
        self.start_time = time.perf_counter() # get starting time, in seconds, as reference point
        self.curr_command = 0
        self.curr_line = 2 # counter that tracks the current line being read from the file, allows us to loop through the file if we reach the end
                        # first line is a header
        self.last_time = 0
        self.time_offset = 0 # an offset used for when you loop through a file
        self.port = COM_Port

    def readline(self):
        lineread = linecache.getline(READFILE, self.curr_line)
        if lineread == '': # if reached EOF
            self.curr_line = 2
            self.time_offset = self.last_time # adjust time offset
            lineread = linecache.getline(READFILE, self.curr_line)
        
        lineread = lineread.strip("\n\r,b'").split(',')
        self.last_time = float( lineread[0] ) + self.time_offset
        lineread[0] = str(self.last_time)

        lineread.append(str(self.curr_command))
        lineread.append('0') # add command and zero-check
        
        ref_time = time.perf_counter()
        while time.perf_counter() - self.start_time < self.last_time :
            if time.perf_counter() - ref_time > self.timeout:
                return '' # if timed out, return without incrementing current time
            pass # block until it's time to send this line or timeout has been reached
        self.curr_line += 1
        return ','.join(lineread)
    
    def write(self, command):
        self.curr_command = command.decode().strip('\n').strip('\r') #decode from UTF-8, then strip endline chars

    def flush(self):
        pass # does nothing, as writing is instantaneous