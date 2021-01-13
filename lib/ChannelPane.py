'''
ChannelPane:

'''

import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import matplotlib.figure as figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

decs = 1 # number of decimal places to which the written output is rounded

class ChannelPane(FigureCanvasTkAgg):
    def __init__(self, graphpanes, mainframe):
        self.graphpanes = graphpanes
        self.num_data_channels = np.size(self.graphpanes.ch_offsets)

        self.fig = figure.Figure()
        super().__init__(self.fig, master=mainframe) 
        self.plot_canvas = self.get_tk_widget()

        self.ch_axes = []
        self.ch_lines = [""]*self.num_data_channels
        self.ch_text = []
        self.ch_min = []
        self.ch_max = []
        self.fig.subplots_adjust(left=0.05, right=0.95, hspace = 0.35)

        self.plot_width = graphpanes.plot_width

        for i in range(self.num_data_channels):
            self.ch_axes.append(self.fig.add_subplot(self.num_data_channels,1,i+1))
            self.ch_text.append(self.ch_axes[i].text(self.plot_width*.1, 0, str(round(self.graphpanes.ch_data[-1][i],decs))+" "+str(self.graphpanes.disp_units[i]),fontsize=12, ha = "right", va = "bottom") )
            self.ch_text[i].set_color(self.graphpanes.ch_colors[i])

            self.ch_max.append(self.ch_axes[i].text(-self.plot_width, 1.02 ,"1.0",fontsize=8, ha = "left", va = "top"))
            self.ch_min.append(self.ch_axes[i].text(-self.plot_width, 0, "0.0",fontsize=8, ha = "left", va = "bottom"))
            self.ch_axes[i].set_ylabel(str(self.graphpanes.disp_units[i]),fontsize=10)
            self.ch_axes[i].set_title(self.graphpanes.ch_names[i],fontsize = 10)
            self.ch_axes[i].set_xlim((-self.plot_width, self.plot_width*.1))
            self.ch_axes[i].set_ylim((0, 1.05))
            self.ch_axes[i].set_xticks([-self.graphpanes.plot_width, 0])
            self.ch_axes[i].tick_params(axis = 'x', labelsize=8)
            self.ch_axes[i].set_yticklabels([])
            self.ch_lines[i], = self.ch_axes[i].plot([0],[0],self.graphpanes.ch_colors[i]) 
        
        self.draw()
        self.plot_canvas.configure(background = "black")

        self.ani = animation.FuncAnimation(  self.fig, self.animate, interval=self.graphpanes.update_interval, blit=True)

    def kill(self):
        self.ani.event_source.stop()

    def animate(self, ind):
        self.graphpanes.update_data() # get most recent Quail data
        # Update plots
        for i in range(self.num_data_channels):
            data_to_consider = self.graphpanes.ch_data[-(int)(self.graphpanes.consider_range*self.graphpanes.elements_on_screen):,i]
            lims = ( 0, max(data_to_consider) + 1E-10 )
            self.ch_max[i].remove() # remove old labels
            self.ch_min[i].remove()
            if self.graphpanes.plot_width != self.plot_width: #if user has adjusted the plot width
                self.ch_axes[i].set_title(self.graphpanes.ch_names[i],fontsize = 10)
                self.ch_axes[i].set_xlim((-self.graphpanes.plot_width, self.graphpanes.plot_width*0.1))
                self.ch_axes[i].set_xticks([-self.graphpanes.plot_width, 0])
                self.ch_axes[i].set_ylabel(str(self.graphpanes.disp_units[i]))
                self.draw()
            self.ch_text[i].set_text(str(round(self.graphpanes.ch_data[-1,i],decs))+" "+str(self.graphpanes.disp_units[i]))
            self.ch_text[i].set_position((self.graphpanes.plot_width*.1, 0))
            self.ch_lines[i].set_data(self.graphpanes.time_data - self.graphpanes.curr_time, ( self.graphpanes.ch_data[:,i] + self.graphpanes.ch_offsets[0,i] )/(lims[1] - lims[0]))
            self.ch_max[i] = self.ch_axes[i].text(-self.graphpanes.plot_width, 1.02, str(int(lims[1])),fontsize=8, ha = "left", va = "top")
            self.ch_min[i] = self.ch_axes[i].text(-self.graphpanes.plot_width, lims[0], str(int(lims[0])),fontsize=8, ha = "left", va = "bottom")
        self.plot_width = self.graphpanes.plot_width
        return self.ch_lines + self.ch_text + self.ch_max + self.ch_min
