##################
'''
This is the dashboard code for interfacing with Quail 1.0.

Current understanding of Quail 1.0 serial output:
7 data channels
1 time channel
1 channel displaying the current command

v0.1: Show a working dash

Luke Upton
Feb 2020

Made for: Stanford Student Space Initiative


Based on:
https://learn.sparkfun.com/tutorials/python-gui-guide-introduction-to-tkinter/all
Complete Dashboard with Plotting Example

'''
##################

# Import Modules Here
import tkinter as tk
import tkinter.font as tkFont

import matplotlib.figure as figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


    # Quail 1.0 Module goes below
from quail_serial import *

# Declare Globals/Parameters Here
update_interval = 2 # Time (ms) between polling/animation updates
max_elements = 1440 # Maximum number of elements to store in plot lists

root = None
dfont = None
frame = None
canvas = None
ax1 = None
temp_plot_visible = None

# Global variable to remember various states
fullscreen = False
temp_plot_visible = True
light_plot_visible = True
ch1_plot_visible = True
ch2_plot_visible = True
ch3_plot_visible = True
ch4_plot_visible = True
ch5_plot_visible = True
ch6_plot_visible = True

solenoid_one = False # Start Solenoids in Off -> Flase 

# Quail object
quail_com_port = 7
#quail = quail(quail_com_port)

###############################################################################
# Functions

# Toggle fullscreen
def toggle_fullscreen(event=None):

    global root
    global fullscreen

    # Toggle between fullscreen and windowed modes
    fullscreen = not fullscreen
    root.attributes('-fullscreen', fullscreen)
    resize(None)   

# Return to windowed mode
def end_fullscreen(event=None):

    global root
    global fullscreen

    # Turn off fullscreen mode
    fullscreen = False
    root.attributes('-fullscreen', False)
    resize(None)

# Automatically resize font size based on window size
def resize(event=None):

    global dfont
    global frame

    # Resize font based on frame height (minimum size of 12)
    # Use negative number for "pixels" instead of "points"
    new_size = -max(12, int((frame.winfo_height() / 15)))
    dfont.configure(size=new_size)

# Toggle the weight plot
def toggle_weight():

    global canvas
    global ax1
    global temp_plot_visible

    # Toggle plot and axis ticks/label
    temp_plot_visible = not temp_plot_visible
    ax1.set_visible(temp_plot_visible)
    ax1.get_yaxis().set_visible(temp_plot_visible)
    canvas.draw()

# Toggle the ch1 plot
def toggle_solenoid_one():
    global solenoid_one
    solenoid_one = not solenoid_one

    if solenoid_one == True:
        button_ch1.configure(bg = "green")
        quail.write_command(11)
        
    else:
        button_ch1.configure(bg = "red")
        quail.write_command(21)
        


# Toggle the ch1 plot
def toggle_ch1():

    global canvas
    global ch1_ax1
    global ch1_plot_visible

    # Toggle plot and axis ticks/label
    ch1_plot_visible = not ch1_plot_visible
    ch1_ax1.set_visible(ch1_plot_visible)
    ch1_ax1.get_yaxis().set_visible(ch1_plot_visible)
    canvas.draw()
    
# Toggle the ch2 plot
def toggle_ch2():

    global canvas
    global ch2_ax1
    global ch2_plot_visible

    # Toggle plot and axis ticks/label
    ch2_plot_visible = not ch2_plot_visible
    ch2_ax1.set_visible(ch2_plot_visible)
    ch2_ax1.get_yaxis().set_visible(ch2_plot_visible)
    canvas.draw()

# Toggle the ch3 plot
def toggle_ch3():

    global canvas
    global ch3_ax1
    global ch3_plot_visible

    # Toggle plot and axis ticks/label
    ch3_plot_visible = not ch3_plot_visible
    ch3_ax1.set_visible(ch3_plot_visible)
    ch3_ax1.get_yaxis().set_visible(ch3_plot_visible)
    canvas.draw()

# Toggle the ch4 plot
def toggle_ch4():

    global canvas
    global ch4_ax1
    global ch4_plot_visible

    # Toggle plot and axis ticks/label
    ch4_plot_visible = not ch4_plot_visible
    ch4_ax1.set_visible(ch4_plot_visible)
    ch4_ax1.get_yaxis().set_visible(ch4_plot_visible)
    canvas.draw()

# Toggle the ch5 plot
def toggle_ch5():

    global canvas
    global ch5_ax1
    global ch5_plot_visible

    # Toggle plot and axis ticks/label
    ch5_plot_visible = not ch5_plot_visible
    ch5_ax1.set_visible(ch5_plot_visible)
    ch5_ax1.get_yaxis().set_visible(ch5_plot_visible)
    canvas.draw()

# Toggle the ch6 plot
def toggle_ch6():

    global canvas
    global ch6_ax1
    global ch6_plot_visible

    # Toggle plot and axis ticks/label
    ch6_plot_visible = not ch6_plot_visible
    ch6_ax1.set_visible(ch6_plot_visible)
    ch6_ax1.get_yaxis().set_visible(ch6_plot_visible)
    canvas.draw()

# Write to quail
def quail_write():
    
    global command_write
    
    
    try:
        val = command_write.get()
        quail.write_command(val)
    except:
        pass



# This function is called periodically from FuncAnimation
def animate(i, ax1, ch1_ax1, ch2_ax1, ch3_ax1, ch4_ax1, ch5_ax1, ch6_ax1, xs, weights, ch1s, ch2s, ch3s, ch4s, ch5s, ch6s, weight, ch1, ch2, ch3, ch4, ch5, ch6):

    # Update data to display temperature and light values
    try:
        quail_data = quail.get_measurements()
        new_ch1     = round(quail_data[0], 2)
        new_ch2     = round(quail_data[1], 2)
        new_ch3     = round(quail_data[2], 2)
        new_ch4     = round(quail_data[3], 2)
        new_ch5     = round(quail_data[4], 2)
        new_ch6     = round(quail_data[5], 2)
        new_weight  = round(quail_data[6], 2)
        timestamp   = round(quail_data[7], 2)/1000
        new_command = int(quail_data[8])
    except:
        pass

    # Update our labels
    weight.set(new_weight)
    ch1.set(new_ch1)
    ch2.set(new_ch2)
    ch3.set(new_ch3)
    ch4.set(new_ch4)
    ch5.set(new_ch5)
    ch6.set(new_ch6)
    command.set(new_command)

    # Append timestamp to x-axis list
    xs.append(timestamp)

    # Append sensor data to lists for plotting
    weights.append(new_weight)
    ch1s.append(new_ch1)
    ch2s.append(new_ch2)
    ch3s.append(new_ch3)
    ch4s.append(new_ch4)
    ch5s.append(new_ch5)
    ch6s.append(new_ch6)

    # Limit lists to a set number of elements
    xs = xs[-max_elements:]
    weights = weights[-max_elements:]
    ch1s = ch1s[-max_elements:]
    ch2s = ch2s[-max_elements:]
    ch3s = ch3s[-max_elements:]
    ch4s = ch4s[-max_elements:]
    ch5s = ch5s[-max_elements:]
    ch6s = ch6s[-max_elements:]

    # Clear, format, and plot temperature values (in front)
    color = 'tab:blue'
    ax1.clear()
    ax1.set_ylabel('Weight (unit)', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.plot(xs, weights, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch1_ax1.clear()
    ch1_ax1.set_ylabel('Ch1 (unit)', color=color)
    ch1_ax1.tick_params(axis='y', labelcolor=color)
    ch1_ax1.plot(xs, ch1s, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch2_ax1.clear()
    ch2_ax1.set_ylabel('Ch2 (unit)', color=color)
    ch2_ax1.tick_params(axis='y', labelcolor=color)
    ch2_ax1.plot(xs, ch2s, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch3_ax1.clear()
    ch3_ax1.set_ylabel('Ch3 (unit)', color=color)
    ch3_ax1.tick_params(axis='y', labelcolor=color)
    ch3_ax1.plot(xs, ch3s, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch4_ax1.clear()
    ch4_ax1.set_ylabel('Ch4 (unit)', color=color)
    ch4_ax1.tick_params(axis='y', labelcolor=color)
    ch4_ax1.plot(xs, ch4s, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch5_ax1.clear()
    ch5_ax1.set_ylabel('Ch5 (unit)', color=color)
    ch5_ax1.tick_params(axis='y', labelcolor=color)
    ch5_ax1.plot(xs, ch5s, linewidth=2, color=color)
    
    color = 'tab:blue'
    ch6_ax1.clear()
    ch6_ax1.set_ylabel('Ch6 (unit)', color=color)
    ch6_ax1.tick_params(axis='y', labelcolor=color)
    ch6_ax1.plot(xs, ch6s, linewidth=2, color=color)

    # Format timestamps to be more readable
    #ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    #fig.autofmt_xdate()

    # Make sure plots stay visible or invisible as desired
    ax1.set_visible(temp_plot_visible)
    ch1_ax1.set_visible(ch1_plot_visible)
    ch2_ax1.set_visible(ch2_plot_visible)
    ch3_ax1.set_visible(ch3_plot_visible)
    ch4_ax1.set_visible(ch4_plot_visible)
    ch5_ax1.set_visible(ch5_plot_visible)
    ch6_ax1.set_visible(ch6_plot_visible)

# Dummy function prevents segfault
def _destroy(event):
    pass

###############################################################################
# Main script

# Create the main window
root = tk.Tk()
root.title("Sensor Dashboard")

# Create the main container
frame = tk.Frame(root)
frame.configure(bg='white')

# Lay out the main container (expand to fit window)
frame.pack(fill=tk.BOTH, expand=1)

# Create figure for plotting
fig = figure.Figure(figsize=(2, 2))
fig.subplots_adjust(left=0.1, right=0.8)
ax1 = fig.add_subplot(4, 2, 7)

# Create figure for channel 1
ch1_ax1 = fig.add_subplot(4,2,1)
ch2_ax1 = fig.add_subplot(4,2,2)
ch3_ax1 = fig.add_subplot(4,2,3)
ch4_ax1 = fig.add_subplot(4,2,4)
ch5_ax1 = fig.add_subplot(4,2,5)
ch6_ax1 = fig.add_subplot(4,2,6)

# Instantiate a new set of axes that shares the same x-axis
#ax2 = ax1.twinx()

# Empty x and y lists for storing data to plot later
xs = []
weights = []
ch1s = []
ch2s = []
ch3s = []
ch4s = []
ch5s = []
ch6s = []

# Variables for holding temperature and light data
weight  = tk.DoubleVar()
ch1     = tk.DoubleVar()
ch2     = tk.DoubleVar()
ch3     = tk.DoubleVar()
ch4     = tk.DoubleVar()
ch5     = tk.DoubleVar()
ch6     = tk.DoubleVar()
command = tk.DoubleVar()
command_write = tk.DoubleVar()

# Create dynamic font for text
dfont = tkFont.Font(size=-24)

# Create a Tk Canvas widget out of our figure
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_plot = canvas.get_tk_widget()


# Create other supporting widgets
#label_temp = tk.Label(frame, text='Temperature:', font=dfont, bg='white')
#label_celsius = tk.Label(frame, textvariable=temp_c, font=dfont, bg='white')
#label_unitc = tk.Label(frame, text="C", font=dfont, bg='white')
#label_light = tk.Label(frame, text="Light:", font=dfont, bg='white')
#label_lux = tk.Label(frame, textvariable=lux, font=dfont, bg='white')
#label_unitlux = tk.Label(frame, text="lux", font=dfont, bg='white')
label_current_command = tk.Label(frame, textvariable=command, font = dfont, bg='blue')
label_command = tk.Label(frame, text = "Cur. Cmd:", font=dfont, bg='blue')
#label_write_command = tk.Label(frame, text = "Write:", font=dfont, bg='white')
#button_temp = tk.Button(    frame, 
#                            text="Toggle Temperature", 
#                            font=dfont,
#                            command=toggle_temp)
#button_light = tk.Button(   frame,
#                            text="Toggle Light",
#                            font=dfont,
#                            command=toggle_light)
button_ch1 =    tk.Button(   frame,
                            text="Ox Vent",
                            font=dfont,
                            command=toggle_solenoid_one)
button_ch2 =    tk.Button(   frame,
                            text="Ch. 2",
                            font=dfont,
                            command=toggle_ch2)
button_ch3 =    tk.Button(   frame,
                            text="Ch. 3",
                            font=dfont,
                            command=toggle_ch3)
button_ch4 =    tk.Button(   frame,
                            text="Ch. 4",
                            font=dfont,
                            command=toggle_ch4)
button_ch5 =    tk.Button(   frame,
                            text="Ch. 5",
                            font=dfont,
                            command=toggle_ch5)
button_ch6 =    tk.Button(   frame,
                            text="Ch. 6",
                            font=dfont,
                            command=toggle_ch6)
button_weight = tk.Button(   frame,
                            text="Ch. 7",
                            font=dfont,
                            command=toggle_weight)
button_quit = tk.Button(    frame,
                            text="Quit",
                            font=dfont,
                            command=root.destroy)
button_write = tk.Button(    frame,
                            text="Write",
                            font=dfont,
                            command=quail_write)
                            
                            
entry_command = tk.Entry(frame, width = 7, textvariable=command_write)

# Lay out widgets in a grid in the frame
canvas_plot.grid(   row=0, 
                    column=0, 
                    rowspan=5, 
                    columnspan=8, 
                    sticky=tk.W+tk.E+tk.N+tk.S)
#label_temp.grid(row=0, column=4, columnspan=2)
#label_celsius.grid(row=1, column=4, sticky=tk.E)
#label_unitc.grid(row=1, column=5, sticky=tk.W)
#label_light.grid(row=2, column=4, columnspan=2)
#label_lux.grid(row=3, column=4, sticky=tk.E)
#label_unitlux.grid(row=3, column=5, sticky=tk.W)
#button_temp.grid(row=5, column=0, columnspan=2)
#button_light.grid(row=5, column=2, columnspan=2)
label_current_command.grid(row=6, column=1, columnspan=1)
label_command.grid(row=6, column=0, columnspan=1)
button_write.grid(row=6, column=2, columnspan=1)
entry_command.grid(row=6, column=3, columnspan=1)

button_ch1.grid(row=5,column=0, columnspan=1)
button_ch2.grid(row=5,column=1, columnspan=1)
button_ch3.grid(row=5,column=2, columnspan=1)
button_ch4.grid(row=5,column=3, columnspan=1)
button_ch5.grid(row=5,column=4, columnspan=1)
button_ch6.grid(row=5,column=5, columnspan=1)
button_weight.grid(row=5, column=6, columnspan=1)
button_quit.grid(row=5, column=7, columnspan=1)

# Add a standard 5 pixel padding to all widgets
for w in frame.winfo_children():
    w.grid(padx=5, pady=5)

# Make it so that the grid cells expand out to fill window
for i in range(0, 6):
    frame.rowconfigure(i, weight=1)
for i in range(0, 7):
    frame.columnconfigure(i, weight=1)

# Bind F11 to toggle fullscreen and ESC to end fullscreen
root.bind('<F11>', toggle_fullscreen)
root.bind('<Escape>', end_fullscreen)

# Have the resize() function be called every time the window is resized
root.bind('<Configure>', resize)

# Call empty _destroy function on exit to prevent segmentation fault
root.bind("<Destroy>", _destroy)

# Initialize our sensors
#tmp102.init()
#apds9301.init()

# Call animate() function periodically
fargs = (ax1, ch1_ax1, ch2_ax1, ch3_ax1, ch4_ax1, ch5_ax1, ch6_ax1, xs, weights, ch1s, ch2s, ch3s, ch4s, ch5s, ch6s, weight, ch1, ch2, ch3, ch4, ch5, ch6)
ani = animation.FuncAnimation(  fig, 
                                animate, 
                                fargs=fargs, 
                                interval=update_interval)                              

# Start in fullscreen mode and run
toggle_fullscreen()
root.mainloop()