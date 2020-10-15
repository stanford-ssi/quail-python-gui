# Toggle fullscreen
def toggle_fullscreen(root, fullscreen, frame, event=None):

    # Toggle between fullscreen and windowed modes
    fullscreen = not fullscreen
    root.attributes('-fullscreen', fullscreen)

# Return to windowed mode
def end_fullscreen(root, fullscreen, frame, event=None):

    # Turn off fullscreen mode
    fullscreen = False
    root.attributes('-fullscreen', False)
    resize(frame) 
