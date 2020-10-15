##################
'''
This is the dashboard code for interfacing with Quail 2.0.

Current understanding of Quail 2.0 serial output:
7 data channels
1 time channel
1 channel displaying the current command

v1.0: Selectively plot channels based on drop-down menu. Set button commands from drop-down menu pop-up dialog.

Luke Upton & Max Newport
Feb 2020

Made for: Stanford Student Space Initiative


Based on:
https://learn.sparkfun.com/tutorials/python-gui-guide-introduction-to-tkinter/all
Complete Dashboard with Plotting Example

'''
##################

# Import Modules Here
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as dialog
import numpy as np
import sys, os
from datetime import datetime

import matplotlib.figure as figure
import matplotlib.animation as animation
import matplotlib.style as plotstyle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    # Quail 1.0 Module goes below
from quail_serial import *
from window_size import *
from button_commands import *

# Declare Globals/Parameters Here
time_on_screen = 15 # sec for which data is on the screen before falling off left side
update_interval = 50 # Time (ms) between polling/animation updates
decs = 1 # number of decimal points to show on string output of current channel values
num_command_buttons = 10 # number of command buttons
num_data_channels = 7 # number of data channels (doesn't include time or command channels)
channel_names = ["Ox Tank Pressure", "Fuel Tank Pressure", "Ox Source Pressure","Fuel Source Pressure","CC Pressure","Ox Manifold Pressure","Load Cell"]
units = ["psi","psi","psi","psi","psi","psi","lbs"] # units for the channels, length should equal num_data_channels
test_name = "GUI_TEST"

## Initialize GUI objects
plot_canvas = None
focus_frame = None
focus_sel_frame = None
button_frame = None
cmd_frame = None
colors = ["#a83232", "#faa352", "#9630c2","#c230a0","#a561ff","#3124b5","#008035"]

root = tk.Tk()
dfont = None
frame = None
ax1 = None
data_f = None

# Build/Initialize data structures
max_elements = int(time_on_screen/(update_interval/1000)) # Maximum number of elements to store in plot lists
consider_range = max_elements
data = np.zeros((max_elements,1 + num_data_channels)) # create data matrix with column for time + data_streams
ch_ax = []
focus_ax = []
buttons = []
focus = [0, 1] # initial channels set up on focus figures

commands = [] # text shown on buttons, correspond to functions
for i in range(num_command_buttons):
    commands.append(tk.StringVar())
    commands[i].set("-")

ch_vals = [] # most recent value of data
for i in range(num_data_channels):
    ch_vals.append(tk.DoubleVar())
    ch_vals[i].set(0.0)

fullscreen = False
recording = False
record_to = None
now=datetime.now()

# Quail object
quail_com_port = 7
#quail = quail(quail_com_port)

###############################################################################
# Functions

def kill():
    ani.event_source.stop()
    ani2.event_source.stop()

def reset_plots():
    global data
    data[:,:-1] = np.zeros((max_elements,num_data_channels))
    red()

def record():
    global recording
    recording = not recording

def scale_recent():
    global consider_range
    consider_range = min(int(0.05*max_elements),2)

def scale_all():
    global consider_range
    consider_range = max_elements

def change_test_name():
    global test_name
    new_name = dialog.askstring("Get New Test Name","Please enter a valid file name (no special chars) : ")
    if new_name != None:
        test_name = new_name

def set_plot_width():
    global update_interval, max_elements, time_on_screen, data, num_data_channels
    time_on_screen = dialog.askfloat("Change Plot Width", "Enter new time-width of plot in seconds:")
    if time_on_screen != None : 
        old_max = max_elements
        max_elements = int(time_on_screen/(update_interval/1000))
        if max_elements > old_max:
            data = np.append(np.zeros((max_elements - old_max, num_data_channels+1)),data,axis = 0)
        elif max_elements < old_max:
            data = data[-max_elements:,:]
        red()

# This function is called periodically from FuncAnimation
def animate(frame, ch_ax, ch_lines, ch_text, ch_min, ch_max):
    global quail, data, max_elements, consider_range, record_to, recording, data_f
    # Update data to display temperature and light values
    try:
        quail_data = quail.get_measurements()
        data = np.append(data,quail_data[0:-1], axis = 0)
        data[-1,-1] = data[-1,-1] /1000 #ms to sec
        new_command = int(quail_data[-1])
    except:
        if recording:
            if record_to == None:
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
                record_to = file_base + "/" + test_name + "___" + d_string + "___" + t_string + ".txt"
                data_f=open(record_to,'w+')
            data_f.write(', '.join( [str(x) for x in data[-1,:]]) + '\n')## THIS SHOULD ACTUALLY WRITE THE QUAIL MEASUREMENTS DIRECTLY!
        elif data_f != None:
            record_to = None
            data_f.close()
        data = np.append(data, [data[-1,-1]*np.power(np.cos(data[-1,-1]/2 * np.arange(1,num_data_channels+2,1)),2)], axis = 0) ### COMMMENT ME OUT IF USING QUAIL\
        data[-1,-1] = data[-2,-1] + update_interval/1000 ### COMMMENT ME OUT IF USING QUAIL\
        new_command = 0

    # Update current command value
    curr_command.set(new_command)

    # Limit lists to a set number of elements
    data = data[-max_elements:,:]

    # Update small plots
    for i in range(num_data_channels):
        lims = (0, max(data[-consider_range:,i])+1e-10)
        if redraw.get():
            ch_ax[i].clear() 
            ch_lines[i], = ch_ax[i].plot(np.arange(0,max_elements,1),data[:,i]/lims[1],c=colors[i])
            ch_text[i] = ch_ax[i].text(max_elements, lims[0], str(round(data[-1][i],decs))+" "+str(units[i]),fontsize=12, ha = "left", va = "bottom") 
            ch_text[i].set_color(colors[i])
            ch_ax[i].set_xlim((0, max_elements*1.15))
            ch_ax[i].set_ylim((0,1.1))
            ch_ax[i].set_title(channel_names[i],fontsize = 10)
            ch_ax[i].set_xticklabels([])
            ch_ax[i].set_yticklabels([])
        else: 
            ch_max[i].remove()
            ch_min[i].remove()
        ch_text[i].set_text(str(round(data[-1,i],decs))+" "+str(units[i]))
        ch_lines[i].set_ydata(data[:,i]/lims[1])
        ch_max[i] = ch_ax[i].text(0,0.96,str(int(lims[1])),fontsize=8, ha = "left", va = "top")
        ch_min[i] = ch_ax[i].text(0,lims[0],str(int(lims[0])),fontsize=8, ha = "left", va = "bottom")
    consider_range += 1
    consider_range = min(max_elements,consider_range)
    redraw.set(False)
    return ch_lines + ch_text + ch_max + ch_min

def animate2(frame, focus_ax, focus_lines, focus_text, focus_min, focus_max, focus_titles, focus1, focus2):
    global data, redraw2, consider_range
    focus = [0, 0]
    focus[0] = channel_names.index(focus1.get())
    focus[1] = channel_names.index(focus2.get())
    for i in range(len(focus)):
        j = focus[i]
        lims = (0, max(data[-consider_range:,j])+1e-10)
        if redraw2.get():
            focus_ax[i].clear() 
            focus_lines[i], = focus_ax[i].plot(np.arange(0,max_elements,1),data[:,j]/lims[1],c = colors[j])
            focus_text[i] = focus_ax[i].text(max_elements,lims[0],str(round(data[-1][j],decs))+" "+str(units[j]),fontsize=14, ha = "left", va = "bottom")
            focus_text[i].set_color(colors[j])
            focus_ax[i].set_xlim((0, max_elements*1.2))
            focus_ax[i].set_ylim((0,1.1))
            focus_ax[i].set_xticklabels([])
            focus_ax[i].set_yticklabels([])
        else:
            focus_lines[i].set_ydata(data[:,j]/lims[1])
            focus_max[i].remove()
            focus_min[i].remove()
            focus_titles[i].remove()
            focus_text[i].set_text(str(round(data[-1,j],decs))+" "+str(units[j]))
        focus_text[i].set_color(colors[j])
        focus_titles[i] = focus_ax[i].text(int(max_elements/2),0.98,str(channel_names[j]),fontsize=14, ha = "center", va = "top")
        focus_max[i] = focus_ax[i].text(0,0.99,str(int(lims[1])),fontsize=11, ha = "left", va = "top")
        focus_min[i] = focus_ax[i].text(0,0,str(int(lims[0])),fontsize=11, ha = "left", va = "bottom")
        focus_lines[i].set_color(colors[j])

    redraw2.set(False)
    return focus_lines + focus_text + focus_min + focus_max + focus_titles

        

###############################################################################
#                              Main script                                    #
###############################################################################

# Create the main window title
root.title("Sensor Dashboard")

# Create the main container
frame = ttk.Frame(root)

# Create sub-containers
button_frame = ttk.Frame(frame)
cmd_frame = ttk.Frame(frame)
focus_sel_frame = ttk.Frame(frame)


# Lay out the main container (expand to fit window, place subframes)
frame.pack(fill=tk.BOTH, expand=1)

# Create figure for plotting all channels in small
plotstyle.use('dark_background')
fig = figure.Figure()
ch_ax = []
ch_lines = [""]*num_data_channels
ch_text = []
ch_min = []
ch_max = []
fig.subplots_adjust(left=0.05, right=0.95, hspace = 0.35)

# Create subplot for each channel
for i in range(num_data_channels):
    ch_ax.append(fig.add_subplot(num_data_channels,1,i+1))
    ch_text.append(ch_ax[i].text(max_elements, 0, str(round(data[-1][i],decs))+" "+str(units[i]),fontsize=12, ha = "left", va = "bottom") )
    ch_text[i].set_color(colors[i])
    lims = (0,1)
    ch_max.append(ch_ax[i].text(0,lims[1],str(lims[1]),fontsize=8, ha = "left", va = "top"))
    ch_min.append(ch_ax[i].text(0,lims[0],str(lims[0]),fontsize=8, ha = "left", va = "bottom"))
    ch_ax[i].set_ylabel(str(units[i]),fontsize=10)
    ch_ax[i].set_title(channel_names[i],fontsize = 10)
    ch_ax[i].set_xlim((0, max_elements*1.15))
    ch_ax[i].set_ylim((0,1))
    ch_ax[i].set_xticklabels([])
    ch_ax[i].set_yticklabels([])
    ch_lines[i], = ch_ax[i].plot(np.arange(0,max_elements,1),data[:,i],colors[i])

# Create two larger figures
focus_fig = figure.Figure()
focus_ax = []
focus_text = []
focus_max = []
focus_min = []
focus_titles = []
focus_lines = [""]*2
focus_fig.subplots_adjust(left=0.1, right=0.95, hspace = 0.1)

for i in range(2):
    focus_ax.append(focus_fig.add_subplot(2,1,i+1))
    focus_text.append(focus_ax[i].text(max_elements,0,str(round(data[-1][i],decs))+" "+str(units[i]),fontsize=14, ha = "left", va = "bottom"))
    focus_text[i].set_color(colors[i])
    lims = (0,1)
    focus_max.append(focus_ax[i].text(0,lims[1],str(lims[1]),fontsize=11, ha = "left", va = "top"))
    focus_min.append(focus_ax[i].text(0,lims[0],str(lims[0]),fontsize=11, ha = "left", va = "bottom"))
    focus_titles.append(focus_ax[i].text(int(max_elements/2),0.98*lims[1],str(channel_names[i]),fontsize=14, ha = "center", va = "top"))
    focus_ax[i].set_xlim((0, max_elements*1.2))
    focus_ax[i].set_ylim((0,1))
    focus_lines[i], = focus_ax[i].plot(np.arange(0,max_elements,1),data[:,i],colors[i])
    focus_ax[i].set_xticklabels([])
    focus_ax[i].set_yticklabels([])
    focus_ax[i].tick_params(axis="y",direction="in", pad=-22)

# Create Tk Canvas widgets out of our figures
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.show()
plot_canvas = canvas.get_tk_widget()
plot_canvas.configure(background = "black")
canvas = FigureCanvasTkAgg(focus_fig, master=frame)
canvas.show()
focus_frame = canvas.get_tk_widget()
focus_frame.configure(background = "black")

# Add items to focus select frame, where users choose which channels they want plotted on the big plots
focus1 = tk.StringVar(focus_sel_frame)
focus1.set(channel_names[0])
focus2 = tk.StringVar(focus_sel_frame)
focus2.set(channel_names[1])
focus1_drop = ttk.OptionMenu(focus_sel_frame,focus1, channel_names[0], *tuple(channel_names))
focus2_drop = ttk.OptionMenu(focus_sel_frame,focus2, channel_names[1], *tuple(channel_names))
focus1_label = ttk.Label(focus_sel_frame,text = "Upper Figure Channel: ")
focus2_label = ttk.Label(focus_sel_frame,text = "  Lower Figure Channel: ")
focus1_label.pack(side=tk.LEFT)
focus1_drop.pack(side=tk.LEFT)
focus2_label.pack(side=tk.LEFT)
focus2_drop.pack(side=tk.LEFT)

# Add items to command frame, where user can input integer quail command value
curr_command = tk.DoubleVar() #variable storing the command that Quail serial returns
command_write = tk.IntVar() #variable storing the command user wants to write to Quail
label_current_command = ttk.Label(cmd_frame, textvariable=curr_command)
label_command = ttk.Label(cmd_frame, text = "Cur. Cmd:")
entry_command = ttk.Entry(cmd_frame, width = 7, textvariable=command_write)
button_write = ttk.Button(cmd_frame, text = "Write", command= lambda: quail.write_command(command_write.get()))
label_current_command.grid(row=0, column=1, columnspan=1, sticky = 'nsew')
label_command.grid(row=0, column=0, columnspan=1, sticky = 'nsew')
button_write.grid(row=1, column=0, columnspan=1, sticky = 'nsew')
entry_command.grid(row=1, column=1, columnspan=1, sticky = 'nsew')
cmd_frame.columnconfigure(0,weight=1)
cmd_frame.columnconfigure(1,weight=1)
cmd_frame.rowconfigure(0,weight=1)
cmd_frame.rowconfigure(1,weight=1)

# Add buttons to button frame
command_button_label = ttk.Label(button_frame, text = "User-Defined Commands:")
command_button_label.grid(row= 0, column = 0, sticky = 'nsew')
for i in range(len(commands)):
    c = commands[i]
    buttons.append(ttk.Button( button_frame, textvariable=c, command=lambda:get_defined_commands(c.get())))
    buttons[i].grid(row= i+1, column = 0, sticky = 'nsew')   
    button_frame.rowconfigure(i+1, weight=1) 
button_frame.columnconfigure(0,weight=1)

# Lay out subframes in the primary frame
cols = 15
rows = 7
plot_canvas.grid(   row=0, column=0, rowspan=7, columnspan=7, sticky='nsew')
focus_sel_frame.grid( row=0, column=7, rowspan=1, columnspan=8, sticky='nsew')
focus_frame.grid( row =1, column=7, rowspan=6, columnspan=7, sticky='nsew')
button_frame.grid( row =1, column=14, rowspan=5, columnspan=1, sticky='nsew')
cmd_frame.grid(    row =6, column=14, rowspan=1, columnspan=1, sticky='nsew')
for i in range(cols):
    frame.columnconfigure(i, weight = 1 )
for i in range(rows):
    frame.rowconfigure(i, weight = 1 )

# Add a standard 5 pixel padding to all widgets
for w in frame.winfo_children():
    w.grid(padx=5, pady=5)

## Create menu bar
menubar = tk.Menu(root)
commandmenu = tk.Menu(menubar, tearoff=0)
commandmenu.add_command(label="Edit Button Commands", command=lambda: open_command_dialog(commands,buttons))
menubar.add_cascade(label="Commands", menu=commandmenu)
plotmenu = tk.Menu(menubar, tearoff=0)
plotmenu.add_command(label="Reset Plots", command=lambda: reset_plots())
plotmenu.add_command(label="Edit Time Width of Plots", command = lambda: set_plot_width())
plotmenu.add_command(label="Scale To Recent Data", command=lambda: scale_recent())
plotmenu.add_command(label="Scale To All Data", command=lambda: scale_all())
menubar.add_cascade(label="Plotting", menu=plotmenu)
recordmenu = tk.Menu(menubar, tearoff=0)
recordmenu.add_command(label="Start Recording", command=lambda: record())
recordmenu.add_command(label="Stop & Save Recording", command=lambda: record())
recordmenu.add_command(label="Change Test Name", command=lambda: change_test_name())
menubar.add_cascade(label="Record", menu=recordmenu)
root.config(menu=menubar)


# Bind F11 to toggle fullscreen and ESC to end fullscreen, bind click to update
def red():
    redraw.set(True)
    redraw2.set(True)
root.bind('<F11>', lambda event: toggle_fullscreen(root, fullscreen, dfont, frame, event))
root.bind('<Escape>', lambda event: end_fullscreen(root, fullscreen, dfont, frame, event))

# Call kill function to stop plot updating on close
root.bind("<Destroy>", lambda event: kill())

# Call animate() function periodically
redraw = tk.BooleanVar(frame)
redraw.set(False)
redraw2 = tk.BooleanVar(frame)
redraw2.set(False)
fargs = (ch_ax, ch_lines, ch_text, ch_min, ch_max)
ani = animation.FuncAnimation(  fig, animate, fargs=fargs, interval=update_interval, blit=True)
fargs2 = (focus_ax, focus_lines, focus_text, focus_min, focus_max, focus_titles, focus1, focus2)
ani2 = animation.FuncAnimation( focus_fig, animate2, fargs=fargs2, interval=update_interval, blit =True)                       

# Start in fullscreen mode and run
root.tk.call('source', 'black.tcl')
s = ttk.Style()
s.theme_use('black')
toggle_fullscreen(root, fullscreen, frame)
root.mainloop()


## Add permanent abort button, don't allow its function to be changed
## Add PulseTime field above buttons
## Add start recording button and label with status - start -> Stop+Save, label->(Recording...,Waiting to record.)
## Add record handler in animate(), which should write to a time_stamped file a comma-delimited version of quail_measurements if recording
# write "scale to recent" and "scale to all" , "reset plots"
# define string command aliases for quail direct writing, handled if text written instead of number in cmd field
        # also define wait_ handler
        # store aliases in lines in folder (if no file, make one)
        # update quail write command to handle:
        # check if input is number : if so, just send command to quail
        # if not, look for that string in the alias file
            # if found in alias file, read in succeeding codes in line
                # if code casts to int, send to quail
                # else if code starts with w, start wait thread for time = rest of code

        # Make Alias builder/writer:
        # get string up to "=", this is command_alias name - write as first item in line of csv
        # for each string split from result with "+", try to cast to int
        # if can, write as item in line
        # if can't, check if first four non-whitespace chars are "wait" and rest can be converted to double
            # if successful, write w + double as next item