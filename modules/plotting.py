# A class for plotting various graphs

import os, re, datetime, sys, psutil
from statistics import mean, median, stdev
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import messagebox as mbox

from modules.shared_functions import *

class figure_frame(tk.Frame):

    day_abbr = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")
    day_index = 0

    def __init__(self,master,data,errors=[]):
        tk.Frame.__init__(self,master)

    def position(self):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, sticky=tk.N+tk.W+tk.S+tk.E)

        self.plot_figure()

        self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.mpl_connect("axes_leave_event", self.mouse_leave_plot)

        self.label_values = tk.Label(master=self, text="", bg="#ffffff")
        self.label_values.grid(row=1, sticky=tk.W)

        self.label_mousepos = tk.Label(master=self, text="", fg="#777777", bg="#ffffff")
        self.label_mousepos.grid(row=2, sticky=tk.W)

        self.button_subframe = tk.Frame(master=self)
        self.button_subframe.grid(row=3)

        self.button_back = tk.Button(master=self.button_subframe, text="<", \
            command=lambda : self.set_day(-1))
        self.button_back.grid(row=3,column=0)

        self.label_day = tk.Label(master=self.button_subframe, text="day_goes_here")
        self.label_day.grid(row=0,column=1)

        self.button_forward = tk.Button(master=self.button_subframe, text=">", \
            command=lambda : self.set_day(1))
        self.button_forward.grid(row=0,column=2)

    def plot_figure(self):
        # Original Plot
        i = self.day_index
        self.ax.cla()
        self.barplot = self.ax.bar(self.open_times[i],self.data[i],width=0.4)
        self.ax.set_title("{} - Mean={}%".format(day_names[i], \
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

    def hover(self, event):
        # XXX
        if event.inaxes == self.ax:
            self.show_value(event)

    def mouse_leave_plot(self, event):
        # XXX
        self.show_value(None)

    def set_day(self, diff):
        self.day_index = (self.day_index + diff) % 7
        self.label_day.configure(text=self.day_abbr[self.day_index])
        self.plot_figure()

    def show_value(self, event):
        # XXX
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
            # value = round(self.data[self.day_index][time_index],1)
            value = round(self.errors[self.day_index][time_index],1)
        except ValueError:
            value = 0

        hours = str(int(time_pos))
        hours = hours if (len(hours) == 2) else "0" + hours
        minutes = "30" if (time_pos % 1 == 0.5) else "00"
        self.label_values.configure(text="{} {}:{} = {}%".format(\
            day_names[self.day_index], hours, minutes, value))

        # Show relative mouse position, for evaluating lines and such
        self.label_mousepos.configure(text="t={}; y={}%".format(\
            round(x,1), round(y,1)))

    # def plot_figure(self):
    #     self.figure_type = 4
    #     if self.figure_type == 1:
    #         self.plot_figure1()
    #     elif self.figure_type == 2:
    #         self.plot_figure2()
    #     elif self.figure_type == 3:
    #         self.plot_figure3()
    #     elif self.figure_type == 4:
    #         self.plot_figure4()
    #
    # def bar_without_errors(self):
    #     # Original Plot
    #     i = self.day_index
    #     self.ax.cla()
    #     self.barplot = self.ax.bar(self.open_times[i],self.data[i],width=0.4)
    #     self.ax.set_title("{} - Mean={}%".format(day_names[i], \
    #         round(mean(self.data[i]),1)))
    #     self.ax.set_xlim([6,23.5])
    #     max_value = 5*(round(max(map(max,self.data))/5)+1)
    #     total_mean = mean(map(mean, self.data))
    #     self.ax.set_ylim([0,max_value])
    #     self.ax.xaxis.set_ticks(list(range(6,24)))
    #     self.ax.axhline(y=mean(self.data[i]))
    #     self.ax.axhline(y=total_mean, alpha=0.2, color="#ff0000")
    #     self.canvas.draw()
    #
    # def bar_standard_errors(self):
    #     # Original Plot plus standard error bars
    #     i = self.day_index
    #     self.ax.cla()
    #     self.barplot = self.ax.bar(self.open_times[i],self.data[i], \
    #         yerr=self.errors[i],width=0.4)
    #     self.ax.set_title("{} - Mean={}%".format(day_names[i], \
    #         round(mean(self.data[i]),1)))
    #     self.ax.set_xlim([6,23.5])
    #     max_value = 5*(round(max(map(max,self.data))/5)+1)
    #     total_mean = mean(map(mean, self.data))
    #     self.ax.set_ylim([0,max_value])
    #     self.ax.xaxis.set_ticks(list(range(6,24)))
    #     self.ax.axhline(y=mean(self.data[i]))
    #     self.ax.axhline(y=total_mean, alpha=0.2, color="#ff0000")
    #     self.canvas.draw()
    #
    # def envelope_line(self):
    #     # Envelope Line Plot
    #     i = self.day_index
    #     self.ax.cla()
    #     self.lineplot = self.ax.plot(self.open_times[i],self.data[i],color="gray")
    #     self.ax.set_title("{} - Mean={}%".format(day_names[i], \
    #         round(mean(self.data[i]),1)))
    #     self.ax.set_xlim([6,23.5])
    #     bottom_line = [self.data[i][x] - self.errors[i][x] for x in range(len(self.open_times[i]))]
    #     top_line = [self.data[i][x] + self.errors[i][x] for x in range(len(self.open_times[i]))]
    #     self.ax.fill_between(self.open_times[i],bottom_line,\
    #         top_line, color="gray",alpha=0.2)
    #     max_value = 5*(round(max(map(max,self.data))/5)+1)
    #     total_mean = mean(map(mean, self.data))
    #     self.ax.set_ylim([0,max_value])
    #     self.ax.xaxis.set_ticks(list(range(6,24)))
    #     self.ax.axhline(y=mean(self.data[i]))
    #     self.ax.axhline(y=total_mean, alpha=0.2, color="#ff0000")
    #     self.canvas.draw()
    #
    # def bar_custom_errors(self):
    #     # Original plot with custom error bars
    #     i = self.day_index
    #     self.ax.cla()
    #     self.barplot = self.ax.bar(self.open_times[i],self.data[i],width=0.4)
    #     elevation = [self.data[i][x] - self.errors[i][x]/2 for x in range(len(self.data[i]))]
    #     self.errplot = self.ax.bar(self.open_times[i],self.errors[i],\
    #         bottom=elevation,width=0.4,alpha=0.3,color="red")
    #     self.ax.set_title("{} - Mean={}%".format(day_names[i], \
    #         round(mean(self.data[i]),1)))
    #     self.ax.set_xlim([6,23.5])
    #     max_value = 5*(round(max(map(max,self.data))/5)+1)
    #     total_mean = mean(map(mean, self.data))
    #     self.ax.set_ylim([0,100])
    #     self.ax.xaxis.set_ticks(list(range(6,24)))
    #     self.ax.axhline(y=mean(self.data[i]))
    #     self.ax.axhline(y=total_mean, alpha=0.2, color="green")
    #     self.canvas.draw()
