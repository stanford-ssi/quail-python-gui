#####################
'''
Module for talking to quail.  Sends and receives information.

Current structure assumes data sent over serial in the following CSV format:

time, CH1, CH2, CH3, CH4, CH5, CH6, last_command, zerocheck

Luke Upton + Max Newport
Oct 2020

'''
#####################

# Import Serial Interfacing Module
import serial
import threading
import multiprocessing as mp
import tkinter.simpledialog as dialog
import numpy as np
import sys, os
from datetime import datetime
from lib.QuailEmulator import QuailEmulator

QUAIL_TIMEOUT = 0.1 # duration of time before readline() gives up
QUAIL_NUM_ELEMENTS = 1 + 6 + 1 + 1 # number of comma-delimited items expected on serial line (time, 6 data channels, last command, zerocheck)

class quail:
    ### The Quail class has three primary objects that interact with the serial port:
    ###
    ### data_process : the data process is inherits the multiprocessing Process class, allowing it to be run in parallel
    ### with the recording/GUI process that handles recording/displaying the data recieved. This ensures that no inbound serial messages are
    ### missed - the method waits for an inbound dataline on the serial port, pushes it to a queue to be displayed (and to a different queue 
    ### if that data should be recorded), writes any commands that need to be written and returns to waiting for a serial line.
    ###
    ### command_thread : the command thread runs on the data process stream as a thread. Python's GIL ensures that two threads on the same process
    ### never execute simultaneously, so no conflict can occur over serial port usage with blocking read/writes. This thread starts and terminates with
    ### the data process.
    ###
    ### record_thread : the record thread runs on the same processor as the primary GUI, and (when activated) offloads data from the recording queue
    ### and writes it to a user-specified data file. Making this a thread allows GUI updating and recording to happen "simultaneously" (during time
    ### between GUI updates, the recording thread can work).

    def __init__(self, mainwindow, COM_Port=11, baud_rate =115200):
        # Establish connection
        if COM_Port < 0: # an un-realistic COM_Port request connects you to the Quail Emulator
            self.serial = QuailEmulator('COM{}'.format(COM_Port), timeout=QUAIL_TIMEOUT)
            mainwindow.title("Quail Dashboard | Connected to Quail Emulator...")
        else:
            mainwindow.title("Quail Dashboard | COM{}".format(COM_Port))
            try:
                self.serial = serial.Serial('COM{}'.format(COM_Port), timeout=QUAIL_TIMEOUT)
            except:
                self.serial = None

        # Initialize unpickled variables (anything the data and cmd processes don't use)
        self.mainwindow = mainwindow
        self.filename = None # string name/filepath of file to which recorded data should be stored

        # Initialize pickled variables (things that the data and cmd process use that are passed to the new process on start)
        self.num_data_channels = 6 # number of data channels
        self.COM_Port = COM_Port # COM Port used for serial connection, made process-safe via the Value object
        self.kill = mp.Queue(maxsize=1) # flag indicating if the data process is to be terminated (if full, kill process)
        self.recording = mp.Queue(maxsize=1) # flag indicating whether to record data recieved, (if full, record)
        self.COM_queue = mp.Queue(maxsize=1) # flag indicating whether to change serial connection (if full, try to connect at new COM value)   
        self.record_queue = mp.Queue() # internally-used queue to which the data_process pushes and from which the record_thread reads
        self.data_queue = mp.Queue() # queue to which ducer/sensor data is pushed
        self.command_queue = mp.Queue() # queue from which commands are read (GUI pushes commands here)

        # Create processes/threads (does not start the process/thread)
        self.data_process = mp.Process(name = "Quail_DataThread", target = self.data_worker)
        self.record_thread = threading.Thread(name = "Quail_RecordThread", target = self.record_worker)

    def __getstate__(self):
        return self.serial, self.num_data_channels, self.COM_Port, self.kill, self.recording, self.COM_queue, self.record_queue, self.data_queue, self.command_queue

    def __setstate__(self, state):
        self.serial, self.num_data_channels, self.COM_Port, self.kill, self.recording, self.COM_queue, self.record_queue, self.data_queue, self.command_queue = state

    def start_collection(self):
        self.data_process.start() # start the data collection process, which calls data_worker

    def stop_collection(self):
        if self.kill.empty():
            self.kill.put(0) # set the kill flag so that the data collection process and cmd thread terminate after completing the current loop
        self.data_process.join() # wait for the data collection process to terminate
        self.kill.get() # clear the kill queue
        if self.recording.full():
            self.stop_recording() # stop recording if necessary

    def start_recording(self, filename):
        ## Validate filename and add time stamp to path ##
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

        ## Initialize vars and begin recording ##
        self.filename = file_base + "/" + filename + "___" + d_string + "___" + t_string + ".txt" # set file name to the desired path/name
        self.recording.put(0) # turn on recording indicator for data collection process
        self.record_thread.start() # start record thread, calling record_worker
    
    def stop_recording(self):
        self.recording.get() # stop adding new data to the record queue
        self.record_thread.join() # stop the record_thread, allowing it to write any data that remains in the queue before returning
        self.record_thread = threading.Thread(name = "Quail_RecordThread", target = self.record_worker) # re-instantiate the thread so it can be started again

    def record_worker(self):
        if self.filename is not None: # ensure that the filename has been set
            with open(self.filename, "w") as f: # open the write-to file
                while self.recording.full() or not(self.record_queue.empty()): # if recording data or if there's data left to record in the queue
                    if not(self.record_queue.empty()):
                        f.write( self.record_queue.get() ) # if there is an item in the queue, remove it and write it 

    def data_worker(self):
        self.cmd_thread = threading.Thread(name = "Quail_CmdThread", target = self.cmd_worker)
        self.cmd_thread.start() # start the cmd thread
        while self.kill.empty(): # while the process has not been killed
            if self.serial is None or self.COM_queue.full():
                if self.COM_queue.full():
                    self.COM_Port = self.COM_queue.get()
                if self.COM_Port < 0: # an un-realistic COM_Port request connects you to the Quail Emulator
                    self.serial = QuailEmulator('COM{}'.format(self.COM_Port), timeout=QUAIL_TIMEOUT)
                else:
                    try:
                        self.serial = serial.Serial('COM{}'.format(self.COM_Port), timeout=QUAIL_TIMEOUT)
                    except:
                        self.serial = None
                        continue # if connection failed, don't try to read
                self.data_queue.put(0) # put non-list object to indicate that GUI should clear old data (new serial port)

            # Query device for string containing measurement values
            val_string = str(self.serial.readline())

            val_string = val_string.strip("\n\r,b'").split(',') # break the value string apart
            if len(val_string) != QUAIL_NUM_ELEMENTS:
                continue # if string recieved has fewer elements than expected, toss it out
            val_array = [float(val) for val in val_string] # convert measurements to float
            
            if val_array.pop() == 0: # confirm the last item in the serial string is zero before keeping data
                self.data_queue.put(val_array) # add array of data to data_queue
                if self.recording.full():
                    self.record_queue.put(','.join(val_string)+'\n') # add raw comma-delimited string to record queue
        self.cmd_thread.join() # wait for the cmd_thread to finish writing any commands in the queue, then terminate it

    def cmd_worker(self):
        while self.kill.empty() or (self.serial is not None and not(self.command_queue.empty()) ): # while the process is active or while there are commands left to write
            if not self.command_queue.empty() and self.serial is not None : # if self.serial is None, Quail is not connected
                command = self.command_queue.get() # get the command to be written
                self.serial.write((str(command) + '\r\n').encode()) #convert unicode string to utf-8 and send through serial
                self.serial.flush() #waits for output to be written to ensure the message gets through
            
            
    def write_command(self, command):
        try:
            self.command_queue.put(int(command) )
        except:
            try:
                print("Quail object recieved non-integer command, " + str(command))
            except:
                print("Quail recieved a non-integer command")

    def set_COM_port(self):
        newCOM = dialog.askinteger("Edit COM Port", "Enter new COM Port: ")
        if newCOM is not None and newCOM != self.COM_Port: # if this is a new COM Port
            self.COM_Port =  newCOM # update COM_Port value 
            self.COM_queue.put(newCOM) # push to queue so data_process knows to renew serial connection at new port

            if newCOM < 0: 
                self.mainwindow.title("Quail Dashboard | Running Quail Emulator... " )
            else:
                self.mainwindow.title("Quail Dashboard | COM{}".format(newCOM))
            
            

            
        
        

