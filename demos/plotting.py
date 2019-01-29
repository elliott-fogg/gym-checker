from matplotlib import pyplot

# Use the left and right keys to flip between values
# Use the up and down keys to flip between types
# Types are Total Average, Term Time Only, Weekly, Daily, Day Type

Data1 = range(20)
Data2 = range(21,40)

toggle = True

def onclick(event):
    global toggle

    toggle = not toggle
    event.canvas.figure.clear()

    if toggle:
        event.canvas.figure.gca().plot(Data1)
    else:
        event.canvas.figure.gca().plot(Data2)

    event.canvas.draw()

fig = pyplot.figure()
fig.canvas.mpl_connect('button_press_event', onclick)

pyplot.plot(Data1)
pyplot.show()
