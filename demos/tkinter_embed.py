import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

def strikethrough(text):
    return '\u0336'.join(text) + '\u0336'

root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

# toolbar = NavigationToolbar2Tk(canvas, root)
# toolbar.update()
# canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


button = tkinter.Button(master=root, text="Quit", command=_quit)
button.pack(side=tkinter.BOTTOM)

def CurSelect(event):
    widget = event.widget
    index = widget.curselection()[0]
    value = widget.get(index)
    print(value)

day_matrix = [1,1,1,1,1,1,1]
day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def day_select(event):
    global day_matrix
    widget = event.widget
    index = widget.curselection()[0]
    if day_matrix[index] == 0:
        day_matrix[index] = 1
    else:
        day_matrix[index] = 0
    rewrite_days(widget)

def rewrite_days(widget):
    widget.delete(0,"end")
    for i in range(len(day_names)):
        if day_matrix[i] == 0:
            widget.insert("end",strikethrough(day_names[i]))
            widget.itemconfig("end", foreground="#999999")
        else:
            widget.insert("end",day_names[i])
            # widget.itemconfig("end",bg="green")

lb2 = tkinter.Listbox(master=root,selectmode="SINGLE")
lb2.bind('<<ListboxSelect>>',day_select)
lb2.pack(side="left")

for item in ("Mon","Tue","Wed","Thu","Fri","Sat","Sun"):
    lb2.insert("end",strikethrough(item))

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.
