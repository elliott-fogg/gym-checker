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
root.wm_title("Positioning with Grid in Tk")

# Define the grid

frame1 = tkinter.Frame(root)
frame2 = tkinter.Frame(root)
frame3 = tkinter.Frame(root)
frame4 = tkinter.Frame(root)
frame1.rowconfigure(1,weight=1)
frame4.columnconfigure(1,minsize=50)

frame1.grid(row=0, column=0, sticky=tkinter.N+tkinter.W+tkinter.S+tkinter.E)
#    pady=(0,33))
frame2.grid(row=0, column=1)
frame3.grid(row=1, column=0)
frame4.grid(row=1, column=1)

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

canvas = FigureCanvasTkAgg(fig, master=frame2)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1,)

toolbar = NavigationToolbar2Tk(canvas, frame2)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)

canvas.mpl_connect("key_press_event", on_key_press)

def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate

def CurSelect(event):
    widget = event.widget
    index = widget.curselection()[0]
    value = widget.get(index)
    print(value)

weeks = ["2018-11-05","2018-11-12","2018-11-19","2018-11-26","2018-12-03"]
week_switches = [1 for _ in range(len(weeks))]

def week_select(event):
    global week_switches
    widget = event.widget
    index = widget.curselection()[0]
    if week_switches[index] == 0:
        week_switches[index] = 1
    else:
        week_switches[index] = 0
    rewrite_weeks(widget)

def rewrite_weeks(widget):
    widget.delete(0,"end")
    for i in range(len(weeks)):
        if week_switches[i] == 0:
            widget.insert("end",strikethrough(weeks[i]))
            widget.itemconfig("end", foreground="#999999")
        else:
            widget.insert("end",weeks[i])
            # widget.itemconfig("end",bg="green")

day_count = 0
day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def up_day():
    set_day(1)

def down_day():
    set_day(-1)

def set_day(diff):
    global day_count
    day_count = (day_count + diff) % 7
    l2.configure(text=day_names[day_count])

b1 = tkinter.Button(master=frame4, text="<", command=down_day)
b1.grid(row=0,column=0)

# b2 = tkinter.Button(master=frame4, text="Quit", command=_quit)
# b2.grid(row=0,column=1)
l2 = tkinter.Label(master=frame4, text="day_goes_here")
l2.grid(row=0,column=1)

b3 = tkinter.Button(master=frame4, text=">", command=up_day)
b3.grid(row=0,column=2)

# button = tkinter.Button(master=frame4, text="Quit", command=_quit)
# button.pack(side=tkinter.BOTTOM)

button4 = tkinter.Button(master=frame3, text="Recalculate", command=_quit)
button4.pack()

label = tkinter.Label(master=frame1,text="Selected Weeks:")
label.grid(row=0, sticky=tkinter.W)

lb2 = tkinter.Listbox(master=frame1,selectmode="SINGLE")
lb2.bind('<<ListboxSelect>>',week_select)
#lb2.pack(side="top", fill="both", expand=True)
lb2.grid(row=1, sticky=tkinter.N+tkinter.W+tkinter.S+tkinter.E)

rewrite_weeks(lb2)
set_day(0)

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.
