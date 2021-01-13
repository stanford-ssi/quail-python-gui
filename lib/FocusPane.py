'''
FocusPane:

The graphing pane that shows two zoomed graphs. Users can select which channels are plotted on these zoomed-in
features using two dropdown menus.
'''

import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import matplotlib.figure as figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

decs = 1 # number of decimal places to which the written output is rounded

class FocusPane(ttk.Frame):
    def __init__(self, graphpanes, mainframe):
        self.graphpanes = graphpanes
        self.num_data_channels = np.size(self.graphpanes.ch_offsets)

        self.fig = figure.Figure()
        super().__init__(master=mainframe, padding = 0) 
        self.canvas =FigureCanvasTkAgg(self.fig, master=self) 
        self.plot_canvas = self.canvas.get_tk_widget()

        self.ch_axes = []
        self.ch_lines = [""]*2
        self.ch_text = []
        self.ch_min = []
        self.ch_max = []
        self.ch_titles = []
        self.fig.subplots_adjust(left=0.05, right=0.95, hspace = 0.35)

        self.plot_width = graphpanes.plot_width

        self.focus1 = tk.StringVar(self)
        self.focus1.set(graphpanes.ch_names[0])
        self.focus2 = tk.StringVar(self)
        self.focus2.set(graphpanes.ch_names[1])
        self.focus1_drop = ttk.OptionMenu(self,self.focus1, graphpanes.ch_names[0], *tuple(self.graphpanes.ch_names))
        self.focus2_drop = ttk.OptionMenu(self,self.focus2, graphpanes.ch_names[1], *tuple(self.graphpanes.ch_names))
        self.focus1_label = ttk.Label(self,text = "Upper Figure Channel: ",justify=tk.RIGHT)
        self.focus2_label = ttk.Label(self,text = "  Lower Figure Channel: ",justify=tk.RIGHT)
        self.focus1_label.grid(row = 0, column = 0, rowspan = 1, columnspan = 1, sticky= 'nsew')
        self.focus1_drop.grid(row = 0, column = 1, rowspan = 1, columnspan = 1, sticky= 'nsew')
        self.focus2_label.grid(row = 0, column = 2, rowspan = 1, columnspan = 1, sticky= 'nsew')
        self.focus2_drop.grid(row = 0, column = 3, rowspan = 1, columnspan = 1, sticky= 'nsew')        

        for i in range(2):
            self.ch_axes.append(self.fig.add_subplot(2,1,i+1))
            self.ch_text.append(self.ch_axes[i].text(self.plot_width*.1, 0, str(round(self.graphpanes.ch_data[-1][i],decs))+" "+str(self.graphpanes.disp_units[i]),fontsize=12, ha = "right", va = "bottom") )
            self.ch_text[i].set_color(self.graphpanes.ch_colors[i])

            self.ch_max.append(self.ch_axes[i].text(-self.plot_width, 1.02 ,"1.0",fontsize=8, ha = "left", va = "top"))
            self.ch_min.append(self.ch_axes[i].text(-self.plot_width, 0, "0.0",fontsize=8, ha = "left", va = "bottom"))
            self.ch_titles.append(self.ch_axes[i].text(-self.plot_width/2,1.0,str(self.graphpanes.ch_names[i]),fontsize=14, ha = "center", va = "top"))
            self.ch_axes[i].set_ylabel(str(self.graphpanes.disp_units[i]),fontsize=10)
            self.ch_axes[i].set_xlim((-self.plot_width, self.plot_width*.1))
            self.ch_axes[i].set_ylim((0, 1.05))
            self.ch_axes[i].set_xticks([-self.plot_width, 0])
            self.ch_axes[i].tick_params(axis = 'x', labelsize=8)
            self.ch_axes[i].set_yticklabels([])
            self.ch_lines[i], = self.ch_axes[i].plot([0],[0],self.graphpanes.ch_colors[i]) 
        
        self.canvas.draw()
        self.plot_canvas.configure(background = "black")
        self.plot_canvas.grid(row = 1, column = 0, rowspan = 10, columnspan = 4, sticky = 'nsew')
        self.rowconfigure(10, weight = 1)

        self.ani = animation.FuncAnimation(  self.fig, self.animate, interval=self.graphpanes.update_interval, blit=True)

    def kill(self):
        self.ani.event_source.stop()

    def animate(self, ind):
        self.graphpanes.update_data() # get most recent Quail data
        focus = [0, 0]
        focus[0] = self.graphpanes.ch_names.index(self.focus1.get())
        focus[1] = self.graphpanes.ch_names.index(self.focus2.get())

        # Update plots
        for i in range(2):
            data_to_consider = self.graphpanes.ch_data[-(int)(self.graphpanes.consider_range*self.graphpanes.elements_on_screen):,focus[i]]
            lims = ( 0, max(data_to_consider) + 1E-10 )
            self.ch_max[i].remove() # remove old labels
            self.ch_min[i].remove()
            self.ch_titles[i].remove()
            if self.graphpanes.plot_width != self.plot_width: #if user has adjusted the plot width
                self.ch_axes[i].set_xlim((-self.graphpanes.plot_width, self.graphpanes.plot_width*0.1))
                self.ch_axes[i].set_xticks([-self.graphpanes.plot_width, 0])
                self.ch_axes[i].set_ylabel(str(self.graphpanes.disp_units[i]))
                self.canvas.draw()
            self.ch_titles[i] = self.ch_axes[i].text(-self.graphpanes.plot_width/2,1.0,str(self.graphpanes.ch_names[focus[i]]),fontsize=14, ha = "center", va = "top")
            self.ch_text[i].set_text(str(round(self.graphpanes.ch_data[-1,i],decs))+" "+str(self.graphpanes.disp_units[focus[i]]))
            self.ch_text[i].set_color(self.graphpanes.ch_colors[focus[i]])
            self.ch_text[i].set_position((self.graphpanes.plot_width*.1, 0))
            self.ch_lines[i].set_data(self.graphpanes.time_data - self.graphpanes.curr_time, (self.graphpanes.ch_data[:,focus[i]] + self.graphpanes.ch_offsets[0,focus[i]] )/(lims[1] - lims[0]))
            self.ch_lines[i].set_color(self.graphpanes.ch_colors[focus[i]])
            self.ch_max[i] = self.ch_axes[i].text(-self.graphpanes.plot_width, 1.02, str(int(lims[1])),fontsize=8, ha = "left", va = "top")
            self.ch_min[i] = self.ch_axes[i].text(-self.graphpanes.plot_width, lims[0], str(int(lims[0])),fontsize=8, ha = "left", va = "bottom")
        self.plot_width = self.graphpanes.plot_width
        return self.ch_lines + self.ch_text + self.ch_max + self.ch_min + self.ch_titles
