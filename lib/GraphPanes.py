import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as dialog
import time
import matplotlib.animation as animation
import matplotlib.style as plotstyle
import numpy as np
import lib.units as units

from lib.FocusPane import FocusPane
from lib.ChannelPane import ChannelPane

INITIAL_DATA_WIDTH = 10.0 # the initial number of seconds displayed on the plots
MAX_DATA_WIDTH = 30.0 # the maximum number of seconds that can be displayed on the plots
MIN_DATA_WIDTH = 1.0  # the minimum number of seconds that can be displayed on the plots

initial_ch_names = ["Nitrous Supply Pressure", "CC Manifold Pressure", "Fuel Tank Pressure","Ox Tank Pressure","Ox Manifold Pressure","Load Cell"]
initial_ch_units = ["psi","psi","psi","psi","psi","lbf"]


## TODO: Add more colors for plotting/mod op
##       Scale based only on data that is in-frame (track last index removed from data)
##       
class GraphPanes:
    ''' GraphPanes is an owner class for the FocusPane and ChannelPane objects, which plot Quail data live. To allow for data to not be
        duplicated between these two plotting classes, the GraphPanes object owns the Quail data that is stored locally. '''
    def __init__(self, mainframe, quail):
        self.mainframe = mainframe # the primary frame of the MainWindow
        self.quail = quail  # the quail object associated with the MainWindow

        self.plot_width = INITIAL_DATA_WIDTH # the width of the graphs, in secs
        self.ch_offsets = np.zeros((1, quail.num_data_channels)) # channel offsets (used for taring or biasing data in the y-direction), same unit as the data
        self.time_data = np.zeros((1, 1)) # the time data, in seconds
        self.ch_data = np.zeros((1, quail.num_data_channels)) # the channel data, with units determined by ch_units
        self.last_command = tk.IntVar() # the Tk var that stores the most recent command that Quail saw
        self.last_command.set(0) # by default, this is set to zero

        self.reference_time = 0 # perf_counter time when last data point was used
        self.curr_time = 0 # time of most recent data point + elapsed time since then

        self.ch_names = initial_ch_names # display titles of plots
        if len(self.ch_names) < self.quail.num_data_channels:
            self.ch_names += ['']*(self.quail.num_data_channels - len(self.ch_names))
        self.ch_units = initial_ch_units # units of the data stored in ch_data, set by what Quail sends over serial
        if len(self.ch_units) < self.quail.num_data_channels:
            self.ch_units += ['unitless']*(self.quail.num_data_channels - len(self.ch_units))
        self.disp_units = self.ch_units.copy() # units displayed on the plots - must be convertible to the corresponding unit in ch_units
        self.ch_colors = ["#a83232", "#faa352", "#9630c2","#c230a0","#a561ff","#3124b5"] # colors used on the plots
        if len(self.ch_colors) < self.quail.num_data_channels:
            self.ch_colors += self.ch_colors[0:(self.quail.num_data_channels - len(self.ch_names))]
        self.update_interval = 50 # time (ms) between polling/animation updates
        
        self.consider_range = 1.0 # the percentage of data elements on screen to be considered for y-axis scaling
        self.elements_on_screen = 1 # the number of elements displayed onscreen at the moment

        plotstyle.use('dark_background') # set all plots to dark mode

        self.focuspane = FocusPane(self, mainframe) # the FocusPane that shows zoomed-in graphs
        self.channelpane = ChannelPane(self, mainframe) # the ChannelPane that shows all channels

    def update_data(self):
        ''' Updates the local data for plotting by dequeuing from Quail, clearing data beyond the scope of the local range,
            and calculating the time since the last Quail data packet. '''
        # Get any new data waiting in Quail's data queue
        i = 0
        while not(self.quail.data_queue.empty()) :
            new_data = self.quail.data_queue.get()
            try:
                new_data[0] # the data must be an iterable to be valid
            except:
                self.reset_plots() # if item recieved is not an iterable, clear the plots (a hacky way to clear the plots)
                continue
            self.time_data = np.append(self.time_data, np.asarray([[new_data[0]]]), axis = 0) 
            if i == 0:
                raw_data = np.asarray([new_data[1:-1]])
            else:
                raw_data = np.append(raw_data, np.asarray([new_data[1:-1]]), axis = 0)
            self.last_command.set(new_data[-1])
            self.reference_time = time.perf_counter() # update reference time
            i += 1
        # Convert raw data from channel unit to display unit
        if i > 0:
            converted_data = np.zeros_like(raw_data)
            for j in range(self.quail.num_data_channels):
                converted_data[:, j] = units.convert(raw_data[:, j], self.ch_units[j], self.disp_units[j])
            self.ch_data = np.append(self.ch_data, converted_data, axis = 0)

            # Update the number of elements on screen
            self.elements_on_screen += i
            while ( self.curr_time - self.time_data[-self.elements_on_screen,:] ) > self.plot_width and self.elements_on_screen > 1:
                self.elements_on_screen -= 1

        # Clear any data that goes beyond the maximum width that can be displayed onscreen
        while self.time_data[-1,0] -  self.time_data[0,0] > MAX_DATA_WIDTH and np.size(self.time_data) > 1:
            self.time_data = self.time_data[1:, :]
            self.ch_data = self.ch_data[1:, :]
        self.elements_on_screen = min(self.elements_on_screen, np.size(self.time_data) )
        # Update curr_time to be time of most recent data point + elapsed time since then
        self.curr_time = self.time_data[-1,:] + time.perf_counter() - self.reference_time

    def kill(self):
        ''' Function that ends the animation loop for each plotting pane, to prevent an attempt to refresh a non-existent plot. '''
        self.focuspane.kill()
        self.channelpane.kill()

    def set_plot_width(self):
        ''' Opens dialog to set the width of the plot, in seconds. The value is constrained between a max and min value
            defined at the top of the screen. '''
        time_on_screen = dialog.askfloat("Change Plot Width", "Enter new time-width of plot in seconds:")
        if time_on_screen != None : 
            self.plot_width = max( min( time_on_screen, MAX_DATA_WIDTH), MIN_DATA_WIDTH )
        
        self.elements_on_screen = 1
        while ( self.curr_time - self.time_data[-self.elements_on_screen-1,:] ) < self.plot_width and self.elements_on_screen > 1 and self.elements_on_screen < np.size(self.time_data):
                self.elements_on_screen += 1

    def scale_recent(self):
        ''' Adjusts what percentage of the local data available contributes to the y-axis scaling, to 25%. '''
        self.consider_range = 0.25

    def scale_all(self):
        ''' Adjusts what percentage of the local data available contributes to the y-axis scaling, to 100%. '''
        self.consider_range = 1.0

    def tare_ch(self, ch_index):
        ''' Tares the Ch. (ch_index + 1) based on the most recent channel data. 
            Note this is equivalent to setting the offset to the negative of the ch data '''
        self.ch_offsets[0, ch_index] = - self.ch_data[-1, ch_index]

    def untare_all(self):
        ''' Untares all the plots. '''
        self.ch_offsets = np.zeros_like(self.ch_offsets)

    def reset_plots(self):
        ''' Clears time and channel data and untares the plots. '''
        self.time_data = np.zeros((1, 1))
        self.ch_data = np.zeros((1, self.quail.num_data_channels))
        self.elements_on_screen = 1
        self.untare_all()

    def set_offsets(self):
        ''' Opens dialog to adjust channel offsets. '''
        win = tk.Toplevel()
        win.grab_set()
        win.wm_title("Update Channel Offset Dialog")
        newvals = []
        for i in range(np.size(self.ch_offsets)):
            l = tk.Label(win, text="Ch #"+str(i+1)+" -- "+ self.ch_names[i] +" offset = ")
            l.grid(row=i, column=0)
            var = tk.DoubleVar(win)
            var.set(self.ch_offsets[0,i])
            b = ttk.Entry(win, width = 7, textvariable =var)
            b.grid(row=i,column=1)
            newvals.append(var)
        update = tk.Button(win,text = "Update Offsets",command = lambda: update_buttons(newvals))
        update.grid(row = self.quail.num_data_channels, column = 1)
        def update_buttons(newvals):
            for i in range(np.size(self.ch_offsets)):
                try:
                    d = newvals[i].get()
                except:
                    d = 0
                self.ch_offsets[0,i] = d # update stringvars with new button functions 

    def set_chunits(self):
        ''' Opens dialog to change channel units and display units. '''
        win = tk.Toplevel()
        win.grab_set()
        win.wm_title("Update Channel Units Dialog")
        new_chunits = []
        new_dispunits = []
        disp_drops = []
        valid_units = units.get_available_units()
        for i in range(np.size(self.ch_offsets)):
            l = tk.Label(win, text="Ch #"+str(i+1)+" -- "+ self.ch_names[i] +" Quail Channel Unit = ")
            l.grid(row=i, column=0)
            ch_var = tk.StringVar(win)
            ch_var.set(self.ch_units[i])
            disp_var = tk.StringVar(win)
            disp_var.set(self.disp_units[i])
            l2 = tk.Label(win, text=" Display Unit = ")
            disp_entry = ttk.OptionMenu(win, disp_var, self.disp_units[i], *(units.get_compatible_units(self.ch_units[i])))
            ch_entry = ttk.OptionMenu(win, ch_var, self.ch_units[i], *valid_units, command= lambda x, i=i: validate_ch_unit(x, i) )
            l2.grid(row=i, column=2)
            disp_entry.grid(row=i,column=3)
            ch_entry.grid(row=i,column=1)
            new_chunits.append(ch_var)
            new_dispunits.append(disp_var)
            disp_drops.append(disp_entry)
        update = tk.Button(win,text = "Update Units",command = lambda: update_units(new_chunits, new_dispunits))
        update.grid(row = self.quail.num_data_channels, column = 3)

        def validate_ch_unit(selected_unit, index):
            '''Child functon that is called upon focusout of ch_entry, adjusts the available disp units. '''
            #new_chunits[index].set(selected_unit)

            # Update dropdown to get compatible units, and if disp_unit is not in that list, change it to match ch_unit
            old_disp_unit = new_dispunits[index].get()
            menu = disp_drops[index]["menu"]
            menu.delete(0, 'end')
            disp_flag = False
            for unit in units.get_compatible_units(selected_unit):
                menu.add_command(label = unit, command = lambda x=unit: new_dispunits[index].set(x))
                if unit.casefold() == old_disp_unit.casefold():
                    disp_flag = True # if the disp unit is still valid with the new unit, chang the flag
            if not disp_flag:
                new_dispunits[index].set(selected_unit) # if disp unit is no longer a compatabile unit, set it to be same as ch_unit
            return True

        def update_units(new_chunits, new_dispunits):
            ''' Child function that is called upon the Update button press. '''
            for i in range(self.quail.num_data_channels):
                # If disp unit has changed, convert old data to the new display unit
                new_disp_unit = new_dispunits[i].get()
                if new_disp_unit.casefold() != self.disp_units[i].casefold():
                    self.ch_data[:,i] = units.convert(self.ch_data[:,i], self.disp_units[i], new_disp_unit)
                # Update units in lists
                self.ch_units[i] = new_chunits[i].get()
                self.disp_units[i] = new_disp_unit
                
            # Force channelpane & focuspane to redraw full plots to update plot axis labels on next animation
            self.focuspane.plot_width = 0
            self.channelpane.plot_width = 0

    def set_chnames(self):
        ''' Opens dialog to change channel names. '''
        win = tk.Toplevel()
        win.grab_set()
        win.wm_title("Update Channel Names Dialog")
        newnames = []
        for i in range(np.size(self.ch_offsets)):
            l = tk.Label(win, text="Ch #"+str(i+1)+" = ")
            l.grid(row=i, column=0)
            var = tk.StringVar(win)
            var.set(self.ch_names[i])
            b = ttk.Entry(win, width = 20, textvariable =var)
            b.grid(row=i,column=1)
            newnames.append(var)
        update = tk.Button(win,text = "Update Names",command = lambda: update_names(newnames))
        update.grid(row = self.quail.num_data_channels, column = 1)
        def update_names(newnames):
            ''' Child function that is called upon the Update button press. '''
            # Record the current channels displayed in the FocusPane
            old_ind1 = self.ch_names.index(self.focuspane.focus1.get())
            old_ind2 = self.ch_names.index(self.focuspane.focus2.get())
            for i in range(np.size(self.ch_offsets)):
                try:
                    d = newnames[i].get()
                except:
                    d = self.ch_names[i]
                self.ch_names[i] = d # update stringvars with new names
            # Update dropdowns in FocusMenu to reflect new names
            menu1 = self.focuspane.focus1_drop["menu"]
            menu1.delete(0, 'end')
            menu2 = self.focuspane.focus2_drop["menu"]
            menu2.delete(0, 'end')
            for name in self.ch_names:
                menu1.add_command(label = name, command = lambda v=name: self.focuspane.focus1.set(v))
                menu2.add_command(label = name, command = lambda v=name: self.focuspane.focus2.set(v))
            # Ensure that the vars connected to the dropdowns still hold valid names
            self.focuspane.focus1.set(self.ch_names[old_ind1])
            self.focuspane.focus2.set(self.ch_names[old_ind2])
            # Force channelpane to redraw full plots to update plot names on next animation
            self.channelpane.plot_width = 0

