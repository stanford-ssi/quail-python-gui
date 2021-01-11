''' 
MenuBar:

The menu bar at the top of a MainWindow. Does not own any of the functions called.
'''

import tkinter as tk

class MenuBar(tk.Menu):
    def __init__(self, mainwindow):
        super().__init__(master = mainwindow) # initialize using parent constructor, with the mainwindow as the master

        # Quail menu
        # --> Edit COM Port: opens a dialog to change the COM Port that the window reads from
        # --> Edit Ch. Names: opens a dialog to change the names of the data channels
        quailmenu = tk.Menu(self, tearoff=0)
        quailmenu.add_command(label="Edit COM Port", command = mainwindow.quail.set_COM_port)
        quailmenu.add_command(label="Edit Ch. Names", command = mainwindow.graphpanes.set_chnames)
        quailmenu.add_command(label="Edit Ch. Units", command = mainwindow.graphpanes.set_chunits)
        self.add_cascade(label="Quail", menu=quailmenu)

        # Commands menu
        # --> Edit Button Commands: opens a dialog to change which commands are displayed on the button pane
        # --> Define New Command Alias: opens a dialog to add a command alias to the manual cmd pane
        commandmenu = tk.Menu(self, tearoff=0)
        commandmenu.add_command(label="Edit Button Commands", command= mainwindow.buttonpane.open_command_dialog )
        commandmenu.add_command(label="Define New Command Alias", command = mainwindow.cmdpane.add_alias )
        self.add_cascade(label="Commands", menu=commandmenu)

        # Plotting menu
        # --> Edit Time Width of Plots: opens a dialog that allows user to change width of all plots
        # --> Scale to Recent Data: y-axis scaling only considers the last 25% of data points on the plot
        # --> Scale to All Data: y-axis scaling considers all data on the plot
        # -------------
        # --> Tare Ch. # : allows user to tare the selected channel, setting the offset to the most recent plot value
        # --> Update Offset Values : opens a dialog that allows user to manually change the y-axis offset values
        # -------------
        # --> Un-tare All Channels: resets all channel offsets to zero, i.e. plots raw y data
        # --> Clear/Reset Plots: untares all channels and clears all local data
        plotmenu = tk.Menu(self, tearoff=0)
        plotmenu.add_command(label="Edit Time Width of Plots", command = mainwindow.graphpanes.set_plot_width )
        plotmenu.add_command(label="Scale To Recent Data", command= mainwindow.graphpanes.scale_recent )
        plotmenu.add_command(label="Scale To All Data", command= mainwindow.graphpanes.scale_all )
        plotmenu.add_separator()
        for i in range(mainwindow.quail.num_data_channels):
            plotmenu.add_command(label="Tare Ch. "+str(i+1)+" = "+mainwindow.graphpanes.ch_names[i], command=lambda a=i: mainwindow.graphpanes.tare_ch(a))
        plotmenu.add_command(label = "Update Offset Values", command = mainwindow.graphpanes.set_offsets)
        plotmenu.add_separator()
        plotmenu.add_command(label="Un-tare All Channels", command= mainwindow.graphpanes.untare_all )
        plotmenu.add_command(label="Clear/Reset Plots", command= mainwindow.graphpanes.reset_plots )
        self.add_cascade(label="Plotting", menu=plotmenu)

        # Recording menu
        # --> Start recording: gets test name from the record pane and starts Quail recording to a time-stamped file with that name
        # --> Stop recording : stops Quail recording
        recordmenu = tk.Menu(self, tearoff=0)
        recordmenu.add_command(label="Start Recording", command= mainwindow.recordpane.start_recording ) 
        recordmenu.add_command(label="Stop Recording", command= mainwindow.recordpane.stop_recording )
        self.add_cascade(label="Record", menu=recordmenu)

        # Limit Protection menu
        # --> Set Red Lines : nothing
        # --> Set Blue Lines : nothing
        # ---------
        # --> Turn Limit Protection On: nothing
        # --> Turn Limit Protection Off: nothing
        linemenu = tk.Menu(self, tearoff=0)
        linemenu.add_command(label="Set Red Line Values", command=lambda: None)
        linemenu.add_command(label="Set Blue Line Values", command=lambda: None)
        linemenu.add_separator()
        linemenu.add_command(label="Turn Limit Protection On", command=lambda: None)
        linemenu.add_command(label="Turn Limit Protection Off", command=lambda: None)
        self.add_cascade(label="Limit Protection", menu=linemenu)