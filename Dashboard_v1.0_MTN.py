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
import csv

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
update_interval = 50 # Time (ms) between polling/animation updates
decs = 1 # number of decimal points to show on string output of current channel values
num_command_buttons = 10 # number of command buttons
num_data_channels = 6 # number of data channels (doesn't include time or command channels)
channel_names = ["Nitrous Supply Pressure", "CC Manifold Pressure", "Fuel Tank Pressure","Ox Tank Pressure","Ox Manifold Pressure","Load Cell"]
units = ["psi","psi","psi","psi","psi","lbs"] # units for the channels, length should equal num_data_channels

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
test_name = tk.StringVar()
test_name.set("Test Name: GUI_TEST") #initial test name, can be updated during runtime
time_on_screen = 15 # sec for which data is on the screen before falling off left side, can be changed in runtime
max_elements = int(time_on_screen/1.57/(update_interval/1000)) # Maximum number of elements to store in plot lists
consider_range = max_elements
data = np.zeros((max_elements,1 + num_data_channels)) # create data matrix with column for time + data_streams
ch_offsets = np.zeros((1,num_data_channels))
ch_ax = []
focus_ax = []
buttons = []
focus = [0, 1] # initial channels set up on focus figures
valid_quail_commands = {"-":0}
with open("Quail_Command_Defs.csv",newline="") as csvfile:
    myreader = csv.reader(csvfile, delimiter=',')
    for row in myreader:
        try:
            valid_quail_commands[row[1] +"\t" + row[0]] = int(row[0])
        except: 
            pass

initial_commands = ["OxVent Pulse", "OxVent Hold", "OxFill Pulse", "OxFill Hold", "OxVent&Fill Pulse",
                    "OxVent&Fill Hold", "FuelPress Pulse", "FuelPress Hold", "Launch","ABORT"] # text shown on buttons, correspond to functions
 # last button is always abort, can't be removed (blows fuel pyro and opens ox vent, closes fill lines)
commands = []
for i in range(num_command_buttons):
    commands.append(tk.StringVar())
    commands[i].set(initial_commands[i])

ch_vals = [] # most recent value of data
for i in range(num_data_channels):
    ch_vals.append(tk.DoubleVar())
    ch_vals[i].set(0.0)

fullscreen = False
recording = False
record_to = None

# Quail object
quail_com_port = 7
# quail = quail(quail_com_port)

###############################################################################
# Functions

def kill():
    ani.event_source.stop()
    ani2.event_source.stop()

def reset_plots():
    global data, ch_offsets
    ch_offsets = np.zeros((1,num_data_channels))
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
        test_name.set("Test Name: "+ new_name)

def set_plot_width():
    global update_interval, max_elements, time_on_screen, data, num_data_channels
    time_on_screen = dialog.askfloat("Change Plot Width", "Enter new time-width of plot in seconds:")
    if time_on_screen != None : 
        old_max = max_elements
        max_elements = int(time_on_screen/1.57/(update_interval/1000))
        if max_elements > old_max:
            data = np.append(np.zeros((max_elements - old_max, num_data_channels+1)),data,axis = 0)
        elif max_elements < old_max:
            data = data[-max_elements:,:]
        red()

def add_alias():
    global valid_quail_commands, command_drop_down, command_selected
    new_alias = dialog.askstring("Add/Replace Quail Command Alias", "Format: <Alias_Name> = <Command1> + wait<wait_val_seconds> + <Command2> + ...")
    new_alias = new_alias.split("=")
    valid_quail_commands[new_alias[0]+"\t"+new_alias[1]] = new_alias[1]
    menu = command_drop_down["menu"]
    menu.delete(0, 'end')
    for key in sorted(valid_quail_commands.keys()):
        menu.add_command(label = key, command = lambda v=key: update_curr_command(v))
    command_selected.set("-")

def update_curr_command(value):
    global command_write
    command_write.set(valid_quail_commands[value])
    command_selected.set("-")

def tare_ch(ch_index):
    global ch_offsets
    ch_offsets[0,ch_index] =  - data[-1,ch_index]  # shift channel value by current value

def set_offsets():
    global ch_offsets
    win = tk.Toplevel()
    win.grab_set()
    win.wm_title("Update Channel Offset Dialog")
    newvals = []
    for i in range(num_data_channels):
        l = tk.Label(win, text="Ch #"+str(i+1)+" -- "+channel_names[i]+" offset = ")
        l.grid(row=i, column=0)
        var = tk.DoubleVar(win)
        var.set(ch_offsets[0,i])
        b = ttk.Entry(win, width = 7, textvariable =var)
        b.grid(row=i,column=1)
        newvals.append(var)
    update = tk.Button(win,text = "Update Offsets",command = lambda: update_buttons(newvals))
    update.grid(row = num_data_channels, column = 1)
    def update_buttons(newvals):
        for i in range(num_data_channels):
            try:
                d = newvals[i].get()
            except:
                d = 0
            ch_offsets[0,i] = d # update stringvars with new button functions 

# This function is called periodically from FuncAnimation
def animate(frame, ch_ax, ch_lines, ch_text, ch_min, ch_max):
    global quail, data, max_elements, consider_range, record_to, recording, data_f
    # Check if need to record data
    if recording:
        if record_to == None:
            record_label.configure(text = "RECORDING",background = colors[0],foreground='white')
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
            record_to = file_base + "/" + test_name.get() + "___" + d_string + "___" + t_string + ".txt"
            data_f=open(record_to,'w+')
    elif data_f != None:
        record_label.configure(text = "Not Recording",background = 'white',foreground=colors[0])
        record_to = None
        data_f.close()

    try:
        quail_data = quail.get_measurements()
        data = np.append(data, quail_data[0:-1], axis = 0)
        data[-1,-1] = data[-1,-1] /1000 #ms to sec
        new_command = int(quail_data[-1])
        if recording:
            data_f.write(', '.join( [str(x) for x in quail_data[:]] + '-' + [str(x) for x in data[-1, :]] ) + '\n')
    except:
        data = np.append(data, [data[-1,-1]*np.power(np.cos(data[-1,-1]/2 * np.arange(1,num_data_channels+2,1)),2)], axis = 0) ### COMMMENT ME OUT IF USING QUAIL\
        data[-1,-1] = data[-2,-1] + update_interval/1000 ### COMMMENT ME OUT IF USING QUAIL\
        new_command = 0 ### COMMMENT ME OUT IF USING QUAIL\
        # print("Failed to read Quail data")
        #pass

    # Update current command value
    curr_command.set(new_command)

    # Limit lists to a set number of elements
    data = data[-max_elements:,:]
    plot_data = data + np.dot( np.ones((max_elements,1)) , np.append(ch_offsets,[[0]],axis=1) )
    # Update small plots
    for i in range(num_data_channels):
        lims = (0, max(plot_data[-consider_range:,i])+1e-10)
        if redraw.get():
            ch_ax[i].clear() 
            ch_lines[i], = ch_ax[i].plot(np.arange(0,max_elements,1),plot_data[:,i]/lims[1],c=colors[i])
            ch_text[i] = ch_ax[i].text(max_elements, lims[0], str(round(plot_data[-1][i],decs))+" "+str(units[i]),fontsize=12, ha = "left", va = "bottom") 
            ch_text[i].set_color(colors[i])
            ch_ax[i].set_xlim((0, max_elements*1.15))
            ch_ax[i].set_ylim((0,1.03))
            ch_ax[i].set_title(channel_names[i],fontsize = 10)
            ch_ax[i].set_xticklabels([])
            ch_ax[i].set_yticklabels([])
        else: 
            ch_max[i].remove()
            ch_min[i].remove()
        ch_text[i].set_text(str(round(plot_data[-1,i],decs))+" "+str(units[i]))
        ch_lines[i].set_ydata(plot_data[:,i]/lims[1])
        ch_max[i] = ch_ax[i].text(1,1.02,str(int(lims[1])),fontsize=8, ha = "left", va = "top")
        ch_min[i] = ch_ax[i].text(1,lims[0],str(int(lims[0])),fontsize=8, ha = "left", va = "bottom")
    consider_range += 1
    consider_range = min(max_elements,consider_range)
    redraw.set(False)
    return ch_lines + ch_text + ch_max + ch_min

def animate2(frame, focus_ax, focus_lines, focus_text, focus_min, focus_max, focus_titles, focus1, focus2):
    global data, redraw2, consider_range
    focus = [0, 0]
    focus[0] = channel_names.index(focus1.get())
    focus[1] = channel_names.index(focus2.get())
    plot_data = data + np.dot( np.ones((max_elements,1)) , np.append(ch_offsets,[[0]],axis=1)) 
    for i in range(len(focus)):
        j = focus[i]
        lims = (0, max(plot_data[-consider_range:,j])+1e-10)
        if redraw2.get():
            focus_ax[i].clear() 
            focus_lines[i], = focus_ax[i].plot(np.arange(0,max_elements,1),plot_data[:,j]/lims[1],c = colors[j])
            focus_text[i] = focus_ax[i].text(max_elements,lims[0],str(round(plot_data[-1][j],decs))+" "+str(units[j]),fontsize=14, ha = "left", va = "bottom")
            focus_text[i].set_color(colors[j])
            focus_ax[i].set_xlim((0, max_elements*1.2))
            focus_ax[i].set_ylim((0,1.05))
            focus_ax[i].set_xticklabels([])
            focus_ax[i].set_yticklabels([])
        else:
            focus_lines[i].set_ydata(plot_data[:,j]/lims[1])
            focus_max[i].remove()
            focus_min[i].remove()
            focus_titles[i].remove()
            focus_text[i].set_text(str(round(plot_data[-1,j],decs))+" "+str(units[j]))
        focus_text[i].set_color(colors[j])
        focus_titles[i] = focus_ax[i].text(int(max_elements/2),1.03,str(channel_names[j]),fontsize=14, ha = "center", va = "top")
        focus_max[i] = focus_ax[i].text(1,1.02,str(int(lims[1])),fontsize=11, ha = "left", va = "top")
        focus_min[i] = focus_ax[i].text(1,0,str(int(lims[0])),fontsize=11, ha = "left", va = "bottom")
        focus_lines[i].set_color(colors[j])

    redraw2.set(False)
    return focus_lines + focus_text + focus_min + focus_max + focus_titles

        

###############################################################################
#                              Main script                                    #
###############################################################################

# Create the main window title
root.title("Sensor Dashboard")

# Create styles that will be used
root.tk.call('source', 'black.tcl')
s = ttk.Style()
s.theme_use('black')
s.configure('Red.TButton', font = ('TkDefaultFont', 14, 'bold'), foreground = 'white', background = colors[0])
s.configure('White.TButton', font = ('TkDefaultFont', 14), foreground = 'black', background = "#d6d6d6")

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
    lims = (0,1.05)
    ch_max.append(ch_ax[i].text(0, 1 ,str(lims[1]),fontsize=8, ha = "left", va = "top"))
    ch_min.append(ch_ax[i].text(0,lims[0],str(lims[0]),fontsize=8, ha = "left", va = "bottom"))
    ch_ax[i].set_ylabel(str(units[i]),fontsize=10)
    ch_ax[i].set_title(channel_names[i],fontsize = 10)
    ch_ax[i].set_xlim((0, max_elements*1.15))
    ch_ax[i].set_ylim(lims)
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
    lims = (0,1.05)
    focus_max.append(focus_ax[i].text(1,1.02,str(lims[1]),fontsize=11, ha = "left", va = "top"))
    focus_min.append(focus_ax[i].text(1,lims[0],str(lims[0]),fontsize=11, ha = "left", va = "bottom"))
    focus_titles.append(focus_ax[i].text(int(max_elements/2),0.98*lims[1],str(channel_names[i]),fontsize=14, ha = "center", va = "top"))
    focus_ax[i].set_xlim((0, max_elements*1.2))
    focus_ax[i].set_ylim(lims)
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
focus1_label = ttk.Label(focus_sel_frame,text = "Upper Figure Channel: ",justify=tk.RIGHT)
focus2_label = ttk.Label(focus_sel_frame,text = "  Lower Figure Channel: ",justify=tk.RIGHT)
focus1_label.grid(row = 1, column = 0, rowspan = 1, columnspan = 1, sticky= 'nsew')
focus1_drop.grid(row = 1, column = 1, rowspan = 1, columnspan = 1, sticky= 'nsew')
focus2_label.grid(row = 1, column = 2, rowspan = 1, columnspan = 1, sticky= 'nsew')
focus2_drop.grid(row = 1, column = 3, rowspan = 1, columnspan = 1, sticky= 'nsew')

record_label = ttk.Label(focus_sel_frame,underline = -1, text = "Not Recording", background = 'white', foreground = colors[0],justify=tk.CENTER)
record_label.grid(row = 0, column = 0, rowspan = 1, columnspan = 1, sticky= 'nsew')
testname_label = ttk.Label(focus_sel_frame,textvariable = test_name)
testname_label.grid(row = 0, column = 1, rowspan = 1, columnspan = 3, sticky= 'nsew')

pulse_time = tk.StringVar()
pulse_time.set("Pulse Time= 1 sec")
pulse_button = ttk.Button(focus_sel_frame,textvariable=pulse_time,command=lambda: update_pulse(pulse_time))
pulse_button.grid(row=1, column=5, rowspan = 1, columnspan = 1, sticky = 'nsew')
focus_sel_frame.rowconfigure(0, weight = 1)
focus_sel_frame.rowconfigure(1, weight = 1)
for i in range(6):
    focus_sel_frame.columnconfigure(i,weight = 1)

# Add items to command frame, where user can input integer quail command value
curr_command = tk.IntVar() #variable storing the command that Quail serial returns
command_write = tk.StringVar() #variable storing the command user wants to write to Quail
command_selected = tk.StringVar()
label_current_command = ttk.Label(cmd_frame, textvariable=curr_command, background = colors[0], foreground = "white")
label_command = ttk.Label(cmd_frame, text = "Cur. Cmd:")
entry_command = ttk.Entry(cmd_frame, width = 7, textvariable=command_write)
button_write = ttk.Button(cmd_frame, text = "Write")
button_write.bind("<Double-Button-1>",lambda event: quail.write_command(command_write.get()))
command_drop_down = ttk.OptionMenu(cmd_frame, command_selected, "-", *sorted(valid_quail_commands.keys()),command = update_curr_command)
label_current_command.grid(row=0, column=1, columnspan=1, sticky = 'nsew')
label_command.grid(row=0, column=0, columnspan=1, sticky = 'nsew')
button_write.grid(row=1, column=0, columnspan=1, sticky = 'nsew')
entry_command.grid(row=1, column=1, columnspan=1, sticky = 'nsew')
command_drop_down.grid(row=2, column=0, columnspan=2, sticky = 'nsew')
cmd_frame.columnconfigure(0,weight=1)
cmd_frame.columnconfigure(1,weight=1)
cmd_frame.rowconfigure(0,weight=1)
cmd_frame.rowconfigure(1,weight=1)

# Add buttons to button frame
command_button_label = ttk.Label(button_frame, text = "User-Defined Commands:")
command_button_label.grid(row= 0, column = 0, sticky = 'nsew')
for i in range(len(commands)):
    c = commands[i]
    my_func = get_defined_commands(c.get())
    if i != len(commands) - 1:
        buttons.append(ttk.Button( button_frame, style = "White.TButton", textvariable = c))
        buttons[i].bind("<ButtonPress-1>", my_func)
    else:
        buttons.append(ttk.Button( button_frame, style = "Red.TButton", textvariable=c))
        buttons[i].bind("<Double-Button-1>", my_func)
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
commandmenu.add_command(label="Define New Command Alias", command = lambda: add_alias())
menubar.add_cascade(label="Commands", menu=commandmenu)
plotmenu = tk.Menu(menubar, tearoff=0)
plotmenu.add_command(label="Edit Time Width of Plots", command = lambda: set_plot_width())
plotmenu.add_command(label="Scale To Recent Data", command=lambda: scale_recent())
plotmenu.add_command(label="Scale To All Data", command=lambda: scale_all())
plotmenu.add_separator()
for i in range(num_data_channels):
    plotmenu.add_command(label="Tare Ch. "+str(i+1)+" = "+channel_names[i], command=lambda a=i: tare_ch(a))
plotmenu.add_command(label = "Update Offset Values", command = set_offsets)
plotmenu.add_separator()
plotmenu.add_command(label="Clear/Reset Plots", command=lambda: reset_plots())
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
toggle_fullscreen(root, fullscreen, frame)
root.mainloop()

############################ TO-DO ############################
# add pad below zero so that some negative data can be seen
