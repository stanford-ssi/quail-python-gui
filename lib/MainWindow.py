#############
''' MainWindow:

    The containing window for the Quail dashboard - when creating the dashboard, this is the object to create an instance of.

    Starts a Quail serial reader and a Tkinter GUI application. The application live-plots Quail data, allowing users to adjust
    scaling, units, and channel names during runtime. Commands can also be sent to Quail via direct numeric input or by functions
    linked to buttons in the application (the functions linked to the assorted buttons can be modified during runtime). 

    Users can record the transmitted Quail data to a local text file, which is time-and-data stamped, along with a user-selected test name 
    identifier.
'''
#############

### Import Tk and threading ###
import tkinter as tk
import tkinter.ttk as ttk
import threading

### Import all the constituent objects that populate the MainWindow ###
from lib.MenuBar import MenuBar
from lib.GraphPanes import GraphPanes
from lib.ButtonPane import ButtonPane
from lib.ManualCmdPane import ManualCmdPane
from lib.RecordingPane import RecordingPane

### Import serial module that handles Quail reading & data collection ###
from lib.quail_serial import quail

class MainWindow(tk.Tk):
    def __init__(self):
        # initialize using the parent constructor to get all parent attributes
        super().__init__() # self is now the standard "root"

        # create the the overall container frame (mainframe), then pack the frame into the main window
        self.mainframe = ttk.Frame(self)
        self.mainframe.pack(fill=tk.BOTH, expand=1) 

        # create Quail object that collects and records serial data
        self.quail = quail(self)

        # Set overall style and create any default styles for Tk Objects #
        self.tk.call('source', 'lib/black.tcl')
        self.style = ttk.Style()
        self.style.theme_use('black')
        self.style.configure('Red.TButton', font = ('TkDefaultFont', 14, 'bold'), foreground = 'white', background = "#a83232")
        self.style.configure('White.TButton', font = ('TkDefaultFont', 14), foreground = 'black', background = "#b6b6b6")

        # create constituent items that make up the main window
        self.graphpanes = GraphPanes(self.mainframe, self.quail) # owner of the focus pane (shows two zoomed channels) and the channel pane (shows all channels)
        self.buttonpane = ButtonPane(self, self.mainframe, self.quail) # command buttons that can be adjusted in a menu bar option
        self.cmdpane = ManualCmdPane(self, self.mainframe, self.quail) # direct Quail interfacing via integer input or selection from a dropdown 
        self.recordpane = RecordingPane(self.mainframe, self.quail) # pane that indicates recording status, time duration of the recording, and test name
        self.menubar = MenuBar(self) # bar at the top of the window with various dropdown menus

        # Bind close event to stop animation updating if the window is closed
        self.bind("<Destroy>", lambda event: self.kill())

        # Pack the frame with constituent components
        self.config(menu = self.menubar)
        num_cols = 5
        num_rows = 10
        self.graphpanes.channelpane.plot_canvas.grid( row=0, column=0, rowspan= num_rows, columnspan= (num_cols - 1)//2, sticky='nsew')
        self.graphpanes.focuspane.grid( row =1, column=(num_cols - 1)//2, rowspan= (num_rows - 1), columnspan= (num_cols - 1)//2, sticky='nsew')
        self.buttonpane.grid( row = 0, column= ((num_cols - 1)//2) * 2, rowspan= (num_rows - 1), columnspan=1, sticky='nsew')
        self.cmdpane.grid( row = (num_rows - 1), column= ((num_cols - 1)//2) * 2, rowspan=1, columnspan=1, sticky='nsew')
        self.recordpane.grid( row = 0, column= (num_cols - 1)//2, rowspan=1, columnspan= (num_cols - 1)//2 , sticky='nsew')

        # set the rows/columns to expand equally to fill space as the window is resized
        for i in range(num_cols):
            self.mainframe.columnconfigure(i, weight = 1 )
        for i in range(1, num_rows):
            self.mainframe.rowconfigure(i, weight = 1 ) # exclude the top row

        # Set fullscreen
        self.fullscreen = True
        self.attributes('-zoomed', True)
        self.attributes('-fullscreen', True)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

    def kill(self):
        # Kill the animation update functions to prevent errors being thrown on window close
        self.graphpanes.kill()

        # Kill Quail data collection, allows recording to finish writing and any commands in-queue will be written #
        self.quail.stop_collection()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen  # Just toggling the boolean
        self.attributes("-fullscreen", self.fullscreen)

    def end_fullscreen(self, event=None):
        self.fullscreen = False
        self.attributes("-fullscreen", False)

    def run(self):
        self.quail.start_collection() # start Quail collection (if fails to connect, will keep trying)
        self.mainloop() # start GUI application running, on close will call kill() function above
        