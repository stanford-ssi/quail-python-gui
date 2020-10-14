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
import tkinter.font as tkFont
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    # Quail 1.0 Module goes below
from quail_serial import *
from window_size import *
from button_commands import *

# Declare Globals/Parameters Here
update_interval = 50 # Time (ms) between polling/animation updates
max_elements = 1440 # Maximum number of elements to store in plot lists
num_command_buttons = 8 # number of command buttons
num_data_channels = 7 # number of data channels (doesn't include time or command channels)
channel_names = ["Ox Tank Pressure", "Fuel Tank Pressure", "Ox Source Pressure","Fuel Source Pressure","CC Pressure","Ox Manifold Pressure","Ox Temp"]
units = ["psi","psi","psi","psi","psi","psi","psi"] # units for the channels, length should equal num_data_channels

## Initialize GUI objects
plot_canvas = None
focus_frame = None
focus_sel_frame = None
button_frame = None
cmd_frame = None

root = tk.Tk()
dfont = None
frame = None
ax1 = None

# Build/Initialize data structures
data = np.zeros((1,1 + num_data_channels)) # create data matrix with column for time + data_streams
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

# Quail object
quail_com_port = 7
#quail = quail(quail_com_port)

###############################################################################
# Functions




# This function is called periodically from FuncAnimation
def animate(frame, ch_ax, data):
    global quail
    # Update data to display temperature and light values
    try:
        quail_data = quail.get_measurements()
        data = np.append(data,quail_data[0:-1], axis = 0)
        data[-1,-1] = data[-1,-1] /1000 #ms to sec
        new_command = int(quail_data[-1])
    except:
        data = np.append(data, data[-1,:]+0.1*np.ones((1,num_data_channels+1)), axis = 0) ### COMMMENT ME OUT IF USING QUAIL\
        data[-1,-1] = data[-2,-1] + update_interval/1000 ### COMMMENT ME OUT IF USING QUAIL\
        new_command = 0

    # Update current command value
    curr_command.set(new_command)

    # Limit lists to a set number of elements
    data = data[-max_elements:,:]

    print(np.shape(data))
    print(data[:,-1])
    print(data[:,1])
    # Update small plots
    for i in range(num_data_channels):
        ch_ax[i].clear()
        ch_ax[i].set_title(str(channel_names[i])+" = "+str(data[-1,i])+" "+str(units[i]),fontsize=10)
        ch_ax[i].plot(data[:,-1],data[:,i],'r')
        ch_ax[i].axes.xaxis.set_ticklabels([])
    
def animate2(frame, focus_ax, data, focus1, focus2):
    focus = [0, 0]
    focus[0] = channel_names.index(focus1.get())
    focus[1] = channel_names.index(focus2.get())
    for i in range(len(focus)):
        focus_ax[i].clear()
        j = focus[i]
        focus_ax[i].set_title(str(channel_names[j])+" = "+str(data[-1,j])+" "+str(units[j]),fontsize=10)
        focus_ax[i].set_ylabel(str(units[j]),fontsize=10)
        focus_ax[i].plot(data[:,-1],data[:,j],'r')
        

        



###############################################################################
# Main script

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
plt.style.use('dark_background')
fig, ch_ax = plt.subplots(7,1, sharex = True)
fig.subplots_adjust(left=0.1, right=0.95, hspace = 0.35)

# Create subplot for each channel
for i in range(num_data_channels):
    ch_ax[i].set_title(str(channel_names[i])+" = "+str(data[-1][i])+" "+str(units[i]),fontsize=10)
    ch_ax[i].set_ylabel(str(units[i]),fontsize=10)
    ch_ax[i].axes.xaxis.set_ticklabels([])

# Create two larger figures
focus_fig, focus_ax = plt.subplots(2,1, sharex= True)
fig.subplots_adjust(left=0.1, right=0.95, hspace = 0.35)
focus_ax[0].set_title(str(channel_names[0])+" = "+str(data[-1][0])+" "+str(units[0]),fontsize=10)
focus_ax[0].set_ylabel(str(units[0]),fontsize=10)
focus_ax[0].axes.xaxis.set_ticklabels([])
focus_ax[1].set_title(str(channel_names[1])+" = "+str(data[-1][1])+" "+str(units[1]),fontsize=10)
focus_ax[1].set_ylabel(str(units[1]),fontsize=10)


# Create dynamic font for text
dfont = tkFont.Font(size=-24)

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
focus1 = tk.StringVar()
focus1.set(channel_names[0])
focus2 = tk.StringVar()
focus2.set(channel_names[1])
focus1_drop = ttk.OptionMenu(focus_sel_frame,focus1,*channel_names)
focus2_drop = ttk.OptionMenu(focus_sel_frame,focus2,*channel_names)
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
for i in range(len(commands)):
    c = commands[i]
    buttons.append(ttk.Button( button_frame, textvariable=c, command=lambda:get_defined_commands(c.get())))
    buttons[i].grid(row= i, column = 0, sticky = 'nsew')   
    button_frame.rowconfigure(i, weight=1) 
button_frame.columnconfigure(0,weight=1)

# Lay out subframes in the primary frame
cols = 15
rows = 6
plot_canvas.grid(   row=0, column=0, rowspan=6, columnspan=7, sticky='nsew')
focus_sel_frame.grid( row=0, column=7, rowspan=1, columnspan=7, sticky='nsew')
focus_frame.grid( row =1, column=7, rowspan=5, columnspan=7, sticky='nsew')
button_frame.grid( row =0, column=14, rowspan=5, columnspan=1, sticky='nsew')
cmd_frame.grid(    row =5, column=14, rowspan=1, columnspan=1, sticky='nsew')
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
root.config(menu=menubar)

# Bind F11 to toggle fullscreen and ESC to end fullscreen
root.bind('<F11>', lambda event: toggle_fullscreen(root, fullscreen, dfont, frame, event))
root.bind('<Escape>', lambda event: end_fullscreen(root, fullscreen, dfont, frame, event))

# Call empty function on exit to prevent segmentation fault
root.bind("<Destroy>", lambda event: None)

# Call animate() function periodically
fargs = (ch_ax, data)
ani = animation.FuncAnimation(  fig, animate, fargs=fargs, interval=update_interval)
fargs2 = (focus_ax, data, focus1, focus2)
# ani2 = animation.FuncAnimation( focus_fig, animate2, fargs=fargs2, interval=update_interval)                       

# Start in fullscreen mode and run
root.tk.call('source', 'black.tcl')
s = ttk.Style()
s.theme_use('black')
toggle_fullscreen(root, fullscreen, frame)
root.mainloop()