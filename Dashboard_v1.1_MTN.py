##################
'''
This is the dashboard code for interfacing with Quail 2.0.

Current understanding of Quail 2.0 serial output:
6 data channels
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

from lib.MainWindow import MainWindow

mainwindow = MainWindow()
mainwindow.run()