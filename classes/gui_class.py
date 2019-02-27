import os, re, datetime, sys, psutil
from statistics import mean, median
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import messagebox as mbox

from classes.shared_functions import *

##### Additional Functions #####################################################

class listboxControl(mouseControl):
    def __init__(self, widget, parent):
        mouseControl.__init__(self, widget, 175)
        self.parent = parent

    def action(self, event):
        if self.button_released_flag:
            if self.double_click_flag:
                self.parent.week_select(self.widget, True)
            else:
                self.parent.week_select(self.widget, False)


##### gui class ################################################################

class gui(tk.Frame):

    ##### Standard Data ####################################################

    open_hours = ((13,46),(13,46),(13,46),(13,46),(13,46),(16,46),(16,43)) # Can be exported to separate file?
    open_times = [list(t/2 for t in range(h[0],h[1])) for h in open_hours]
    day_names = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
    day_abbr = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")
    day_index = 0


    ##### Button Functions #################################################

    def check_escape(self, event):
        if event.keysym == "Escape":
            self.master.quit()
            self.master.destroy()

    def set_day(self, diff):
        self.day_index = (self.day_index + diff) % 7
        self.label_day.configure(text=self.day_abbr[self.day_index])
        self.plot_figure()

    def recalculate(self):
        if sum(self.weeks_selected) == 0:
            mbox.showwarning("No Weeks Selected","Please select at least 1 week")
            return
        self.week_switches = [i for i in self.weeks_selected]
        self.rewrite_weeks()
        self.waitscreen_start()
        self.update()
        self.calculate_data()
        self.plot_figure()
        self.waitscreen_stop()
        self.update()

    def save_weeks(self):
        savefile = data("saved_weeks.csv")
        str_data = [str(c) for c in self.weeks_selected]
        save_data = ",".join(str_data)
        with open(savefile,"w") as f:
            f.write(save_data)

    def load_weeks(self):
        loadfile = data("saved_weeks.csv")
        if not os.path.isfile(loadfile):
            default_file = data("term_weeks.csv")
            if os.path.isfile(default_file):
                with open(default_file, "r") as f:
                    weeks_str = f.read().split(",")
            else:
                mbox.showwarning("ERROR","No 'term_dates.csv' file exists")
                return
        else:
            with open(loadfile,"r") as f:
                weeks_str = f.read().split(",")
        weeks_int = [int(i) for i in weeks_str]
        self.weeks_selected = weeks_int
        self.rewrite_weeks()

    def reset(self):
        loadfile = data("term_weeks.csv")
        if not os.path.isfile(loadfile):
            print(loadfile)
            mbox.showwarning("ERROR","No 'term_dates.csv' file exists")
            return
        else:
            with open(loadfile,"r") as f:
                weeks_str = f.read().split(",")
        weeks_int = [int(i) for i in weeks_str]
        self.weeks_selected = weeks_int
        self.rewrite_weeks()

    def restart_and_update(self):
        result = mbox.askyesno("Update","Restart program and update database?")
        if not result:
            return
        args = sys.argv
        if not (any(x in ("--update","-u") for x in args)):
            args.append("-u")
        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            pass
            #logging.error(e)
        python = sys.executable
        os.execl(python, python, *args)

    def update_database(self):
        self.waitscreen_start()
        self.gc.update_from_aws()
        self.get_week_starts()
        self.rewrite_weeks()
        self.update()
        self.calculate_data()
        self.plot_figure()
        self.waitscreen_stop()
        self.update()
        # End waitscreen

    def hover(self, event):
        if event.inaxes == self.ax:
            self.show_value(event)

    def mouse_leave_plot(self, event):
        self.show_value(None)

    def week_select(self, widget, single):
        index = widget.curselection()[0]
        if single:
            for i in range(len(self.weeks_selected)):
                self.weeks_selected[i] = 0
            self.weeks_selected[index] = 1
        else:
            index = widget.curselection()[0]
            if self.weeks_selected[index] == 0:
                self.weeks_selected[index] = 1
            else:
                self.weeks_selected[index] = 0
        self.rewrite_weeks()


    ##### Follow-up Functions ##############################################

    def rewrite_weeks(self):
        lb = self.lb_weeks
        lb.delete(0,"end")
        for i in range(len(self.week_starts)):
            text = self.week_starts[i]

            if self.week_switches[i] == 0:
                lb.insert("end",strikethrough(text))
            else:
                lb.insert("end",text)

            if self.weeks_selected[i] == 0:
                lb.itemconfig("end",foreground="#999999")

    def show_value(self, event):
        if event == None:
            self.label_values.configure(text="")
            self.label_mousepos.configure(text="")
            return

        # Find the appropriate x_value:
        x, y = event.xdata, event.ydata
        time_pos = round(x * 2) / 2.

        # Get index of time position
        try:
            time_index = self.open_times[self.day_index].index(time_pos)
            value = round(self.data[self.day_index][time_index],1)
        except ValueError:
            value = 0

        hours = str(int(time_pos))
        hours = hours if (len(hours) == 2) else "0" + hours
        minutes = "30" if (time_pos % 1 == 0.5) else "00"
        self.label_values.configure(text="{} {}:{} = {}%".format(\
            self.day_names[self.day_index], hours, minutes, value))

        # Show relative mouse position, for evaluating lines and such
        self.label_mousepos.configure(text="t={}; y={}%".format(\
            round(x,1), round(y,1)))


    ##### Drawing / Positioning ############################################

    def position(self):
        # Base Frames
        self.f1 = tk.Frame(self)
        self.f2 = tk.Frame(self, bg="#ffffff")
        self.f3 = tk.Frame(self)
        self.f4 = tk.Frame(self)

        self.f1.rowconfigure(1,weight=1)
        self.f4.columnconfigure(1,minsize=50)
        self.f2.rowconfigure(0,weight=1)

        self.f1.grid(row=0, column=0, sticky=tk.N+tk.W+tk.S+tk.E)
        self.f2.grid(row=0, column=1)
        self.f3.grid(row=1, column=0)
        self.f4.grid(row=1, column=1)

        # Frame 1
        self.label_select_weeks = tk.Label(master=self.f1,text="Selected Weeks:")
        self.label_select_weeks.grid(row=0, sticky=tk.W)

        self.lb_weeks = tk.Listbox(master=self.f1,selectmode="SINGLE")
        self.lb_weeks.grid(row=1, sticky=tk.N+tk.W+tk.S+tk.E)
        self.lb_weeks_mc = listboxControl(self.lb_weeks, self)

        self.rewrite_weeks()

        self.f5 = tk.Frame(master=self.f1)
        self.f5.grid(row=2)

        self.button_save = tk.Button(master=self.f5, text="Save", \
            command=self.save_weeks)
        self.button_save.pack(side=tk.LEFT)
        self.button_load = tk.Button(master=self.f5, text="Load", \
            command=self.load_weeks)
        self.button_load.pack(side=tk.LEFT)
        self.button_load = tk.Button(master=self.f5, text="Reset", \
            command=self.reset)
        self.button_load.pack(side=tk.RIGHT)

        # Frame 2
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.f2)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, sticky=tk.N+tk.W+tk.S+tk.E)

        self.plot_figure()

        self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.mpl_connect("axes_leave_event", self.mouse_leave_plot)

        self.label_values = tk.Label(master=self.f2, text="", bg="#ffffff")
        self.label_values.grid(row=1, sticky=tk.W)

        self.label_mousepos = tk.Label(master=self.f2, text="", fg="#777777", bg="#ffffff")
        self.label_mousepos.grid(row=2, sticky=tk.W)

        # Frame 3
        self.button_recalc = tk.Button(master=self.f3, text="Recalculate", \
            command=self.recalculate)
        self.button_recalc.pack(side=tk.LEFT)
        self.button_update = tk.Button(master=self.f3, text="UPDATE", \
            command=self.update_database)
        self.button_update.pack(side=tk.LEFT)

        # Frame 4
        self.button_back = tk.Button(master=self.f4, text="<", \
            command=lambda : self.set_day(-1))
        self.button_back.grid(row=0,column=0)

        self.label_day = tk.Label(master=self.f4, text="day_goes_here")
        self.label_day.grid(row=0,column=1)

        self.button_forward = tk.Button(master=self.f4, text=">", \
            command=lambda : self.set_day(1))
        self.button_forward.grid(row=0,column=2)

        # Set positions
        self.grid()

    def plot_figure(self):
        i = self.day_index
        self.ax.cla()
        self.bar_container = self.ax.bar(self.open_times[i],self.data[i],width=0.4)
        self.ax.set_title("{} - Mean={}%".format(self.day_names[i], \
            round(mean(self.data[i]),1)))
        self.ax.set_xlim([6,23.5])
        max_value = 5*(round(max(map(max,self.data))/5)+1)
        total_mean = mean(map(mean, self.data))
        self.ax.set_ylim([0,max_value])
        self.ax.xaxis.set_ticks(list(range(6,24)))
        self.ax.axhline(y=mean(self.data[i]))
        self.ax.axhline(y=total_mean, alpha=0.2, color="#ff0000")
        self.canvas.draw()

    def waitscreen_start(self):
        self.waiting = True
        canvas = self.canvas.get_tk_widget()
        width, height = canvas.winfo_width(), canvas.winfo_height()
        self.waitscreen = tk.Canvas(width=width, height=height, master=self.f2)
        self.waitscreen.create_rectangle(5, 5, width-5, height-5)
        self.waitscreen.create_text(width/2,height/2, \
            text="Recalculating...")

        canvas.grid_forget()
        self.waitscreen.grid(row=0, sticky=tk.N+tk.W+tk.S+tk.E)

    def waitscreen_stop(self):
        self.waiting = False
        canvas = self.canvas.get_tk_widget()
        self.waitscreen.grid_forget()
        canvas.grid(row=0, sticky=tk.N+tk.W+tk.S+tk.E)

    ##### Calculation Functions ############################################

    def get_week_starts(self):
        dates = self.gc.get_uniques("date, day", "date")
        for d in dates:
            if d[1] == "Monday":
                start_date = date(d[0]).value
                break
        for d in reversed(dates):
            if d[1] == "Sunday":
                end_date = date(d[0]).value
                break
        qprint("Data ranges from {} to {}".format(start_date, end_date))
        temp_date = start_date
        week_starts = []
        while True:
            week_starts.append(str(date(temp_date)))
            temp_date += datetime.timedelta(days=7)
            if temp_date > end_date:
                break
        self.week_starts = week_starts

        for fpath in ("saved_weeks.csv", "term_weeks.csv"):
            loadfile = data(fpath)
            if os.path.isfile(loadfile):
                with open(loadfile, "r") as f:
                    weeks_str = f.read().split(",")
        try:
            self.week_switches = [int(i) for i in weeks_str]
            if len(self.week_switches) < len(week_starts):
                self.week_switches += [0] * (len(week_starts) - len(self.week_switches))
        except Error as e:
            qprint("ERROR: Neither saved_weeks.csv or term_weeks.csv found!")
            self.week_switches = [1 for _ in week_starts]
        self.weeks_selected = [i for i in self.week_switches]

    def calculate_data(self):
        data = []

        for d in range(7):
            day_values = []
            for t in self.open_times[d]:
                total = 0
                r_count = 0
                for i in range(len(self.week_starts)):
                    if self.week_switches[i] == 0:
                        continue
                    w_start = date(self.week_starts[i]).value
                    w_end = w_start + datetime.timedelta(days=6)

                    com1 = "SELECT value FROM gymchecker WHERE date BETWEEN {} AND {} ".format(\
                        int(date(w_start)), int(date(w_end)))
                    com2 = "AND time={} AND day='{}'".format(t, self.day_names[d])
                    results = self.gc.x(com1 + com2)
                    try:
                        total += results[0][0]
                        r_count += 1
                    except:
                        # print("Error for: {}".format(com1+com2))
                        pass
                total /= max(1,r_count)
                day_values.append(total)

            data.append(day_values)
        self.data = data


    ##### init function ####################################################

    def __init__(self, master, gc):
        self.gc = gc
        tk.Frame.__init__(self, master)
        master.bind("<KeyPress>", self.check_escape)
        self.get_week_starts()
        self.calculate_data()
        self.position()
        self.set_day(0)
