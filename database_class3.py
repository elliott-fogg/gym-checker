import os, sqlite3, re, json, boto3, decimal, shutil, datetime, sys
from boto3.dynamodb.conditions import Key, Attr
from statistics import mean, median
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import tkinter as tk

##### Utility Functions / Dictionaries #########################################

def rel_path(path):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dirname + "/" + path

## A dictionary for converting from Python types to SQLite Types
sql_type = {
    'str' : 'TEXT',
    'int' : 'INTEGER',
    'float' : 'REAL',
    'bytes' : 'BLOB',
    'NoneType' : 'NULL'
    }

def strikethrough(text):
    return '\u0336'.join(text) + '\u0336'

def arraymax(l):
    return max(map(max,l))

class DecimalEncoder(json.JSONEncoder):
    """DecimalEncoder - A class to translate returned JSON data from AWS that
        uses the Decimal objects for its numbers."""
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

##### DatabaseObject Class #####################################################

class databaseObject(object):

    def __init__(self, file_path, table_name=None, parameters=None):
        self.file_path = file_path
        self.set_file(file_path)
        if table_name != None:
            self.set_table(table_name, parameters)

    def set_file(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

    def set_table(self, table_name, param_array=None):
        if self.check_table_exists(table_name):
            print("Table '{}' already exists".format(table_name))
            self.table = table_name
            self.set_table_params(table_name)
            print("Params: {}".format(self.params_to_text()))
        else:
            if param_array == None:
                print("Cannot create table. No parameters provided")
            else:
                self.create_table(table_name, param_array)

    def transform_parameters(self, param_array):
        param_text = ""
        for param in param_array:
            param_text += "{} {}, ".format(param[0], param[1])
        param_text = param_text[:-2]
        return param_text

    def check_table_exists(self, table_name):
        results = self.query_table_info(table_name)
        if len(results) > 0:
            return True
        else:
            return False

    def set_table_params(self, table_name):
        r = self.query_table_info(table_name)
        self.params, self.param_order = self.params_from_text(\
            re.findall("\((.+)\)",r[0][1])[0])

    def params_from_text(self, param_text):
        params = {}
        param_order = []
        p_pairs = param_text.split(",")
        for p_pair in p_pairs:
            p = p_pair.split()
            params[p[0]] = p[1]
            param_order.append(p[0])
        return (params,param_order)

    def params_to_text(self):
        param_text = ""
        for p in self.params:
            param_text += "{} {}, ".format(p, self.params[p])
        return param_text[:-2]

    def query_table_info(self, table_name=None):
        c = self.cursor
        if table_name == None:
            command = "SELECT name, sql FROM sqlite_master WHERE type='table'"
        else:
            command = \
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND name='{}'".format(\
                table_name)
        c.execute(command)
        r = c.fetchall()
        return r

    def create_table(self, table_name, param_array):
        c = self.cursor
        param_text = self.transform_parameters(param_array)
        command = "CREATE TABLE IF NOT EXISTS {} ({})".format(\
            table_name, param_text)
        c.execute(command)
        self.table = table_name
        self.params, self.param_order = self.params_from_text(param_text)
        print("Creating table - Name: '{}', Params: '{}'".format(\
            table_name, param_text))

    def drop_table(self, table_name):
        c = self.cursor
        command = "DROP TABLE IF EXISTS {}".format(table_name)
        c.execute(command)
        print("Dropped table '{}'".format(table_name))

    def format_data(self, data_json):
        if not isinstance(data_json,list):
            print("Data not in list format. Not JSON form.")
            print("\nDATA:\n{}\n\n".format(data_json))
            return [None,0,None]

        valid_entries = []
        table_keys = set(self.param_order)

        for i in range(len(data_json)):
            entry = data_json[i]

            # Check if entry is in JSON format
            if not isinstance(entry,dict):
                print("Entry {} is not a dict. Not JSON format.".format(i))
                print("ENTRY:\n{}".format(entry))
                continue

            entry_keys = set(entry.keys())
            missing_keys = table_keys - entry_keys
            surplus_keys = entry_keys - table_keys

            if len(missing_keys) + len(surplus_keys) > 0:
                if len(missing_keys) > 0:
                    m_text = "Missing: {}; ".format(missing_keys)
                if len(surplus_keys) > 0:
                    s_text = "Surplus: {}; ".format(surplus_keys)
                print("Entry {} - {}{}".format(i, m_text, s_text))
                print("ENTRY:\n{}".format(entry))
                continue

            # If we've reached here, entry has passed all checks
            valid_entries.append(self.convert_data(entry))

        num_total_entries = len(data_json)
        num_valid_entries = len(valid_entries)
        print("{}/{} entries are valid.".format(num_valid_entries,num_total_entries))
        if num_valid_entries == 0:
            print("No valid entries to input. Aborting.")
            return [None,0,None]
        num_params = len(valid_entries[0])
        valid_entry_array = []

        for entry in valid_entries:
            reordered_entry_array = []
            for p in self.param_order:
                reordered_entry_array.append(entry[p])
            valid_entry_array.append(reordered_entry_array)

        return (valid_entry_array,num_valid_entries,num_params)

    def convert_data(self,data_json):
        # Convert the time
        converted_json = {}
        converted_json["ID"] = data_json["ID"]
        converted_json["day"] = data_json["day"]
        converted_json["time"] = round_time(data_json["time"])
        converted_json["date"] = int("".join(re.findall("(\d+)",data_json["date"])))
        converted_json["value"] = int(re.findall("(\d+)",data_json["value"])[0])
        print(converted_json)
        return converted_json

    def insert_data(self, json_data):
        if self.table == None:
            print("No table selected")
            return
        data_array, num_entries, num_params = self.format_data(json_data)
        if num_entries == 0:
            return
        print("Entries: {}, Params: {}".format(num_entries, num_params))
        c = self.cursor
        q_marks = "(?" + ",?" * (num_params-1) + ")"
        command = "INSERT INTO {} VALUES {}".format(self.table, q_marks)
        if num_entries >= 1:
            c.executemany(command,data_array)
        self.connection.commit()

    def x(self,command):
        try:
            self.cursor.execute(command)
            return self.cursor.fetchall()
        except Exception as err:
            print("EXECUTION FAILED")
            print("Command: {}".format(command))
            print("Error:\n{}".format(err))

    def query(self, query_string):
        return self.x("SELECT * FROM {} WHERE {}".format(self.table, query_string))

    def get_all(self):
        return self.x("SELECT * FROM {}".format(self.table))

    def count_entries(self):
        r = self.x("SELECT count(*) FROM {}".format(self.table))
        return r[0][0]

    def get_uniques(self,distinct_columns,sort_columns=None):
        if sort_columns == None:
            sort_columns = distinct_columns
        r = self.x("SELECT DISTINCT {} FROM {} ORDER BY {}".format(\
            distinct_columns, self.table, sort_columns))
        return r

    def locate_files(self):
        c = self.cursor
        c.execute("PRAGMA database_list")
        rows = c.fetchall()
        for row in rows:
            print(row[0], row[1], row[2])

##### Gymchecker Functions #####################################################

## backup(file_path,shrink_allowed)
# Create a backup of the specified file. If shrink_allowed is False, do not
# overwrite the backup if it would decrease in size (i.e. useful if backing up
# a database that is only supposed to be added to.)
def backup(file_path,shrink_allowed=False):
    try:
        file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        print("No database exists at '{}'. Cannot backup.".format(file_path))
        return

    backup_path = file_path + ".backup"
    try:
        backup_size = os.path.getsize(backup_path)
    except FileNotFoundError:
            print("No backup file for '{}'".format(file_path))
            print("Creating new backup...")
            shutil.copy(file_path,backup_path)
            print("Backup created.")
            return

    print("\nDatabase: {}, Backup: {}".format(file_size,backup_size))
    if backup_size > file_size and not shrink_allowed:
        print("##########")
        print("WARNING: Current version of '{}' is smaller than backup!".format(file_path))
        print("This could potentially indicate that the database has lost information.")
        print("Please check the database before erasing the backup.")
        print("##########")
    else:
        print("Updating backup for '{}'...".format(file_path))
        shutil.copy(file_path,backup_path)
        print("Backup overwritten.")

## update_from_aws_gymchecker(dbObject)
# Takes the specified databaseObject and updates it from the AWS table. Uses the
# ACCESS_ID and ACCESS_KEY from an external file which is not uploaded to Github.
def update_from_aws_gymchecker(dbObject):
    # Load Access Keys
    with open(rel_path("data/private.access_keys"), "r") as f:
        contents = f.read()
    lines = contents.split()
    ACCESS_ID = lines[0].split("#")[0]
    ACCESS_KEY = lines[1].split("#")[0]

    # Setup Resources
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2", \
        aws_access_key_id = ACCESS_ID, aws_secret_access_key = ACCESS_KEY)
    table = dynamodb.Table("GymCheckerData")

    # Find highest ID number in current database
    max_id = dbObject.x("SELECT MAX(ID) FROM {}".format(dbObject.table))[0][0]
    if max_id == None: max_id = 0;
    # Access AWS database
    print("\nAccessing AWS database...")
    raw_response = table.scan(
        FilterExpression=Attr('ID').gt(max_id))
    print("Access complete.")

    # Format results
    print("\nAWS Reponse Metadata:")
    response_data = json.loads(json.dumps(raw_response, indent=4, cls=DecimalEncoder))
    results = response_data.pop("Items")
    current_items = response_data.pop("ScannedCount")
    print(json.dumps(response_data, indent=2))
    print("")

    # Insert results into table
    dbObject.insert_data(results)

    # Check the number of entries in the table
    entries = dbObject.count_entries()
    if entries == current_items:
        print("MATCH - {} entries in local and AWS tables.".format(entries))
        backup(dbObject.file_path)
    else:
        print("ERROR - Entries in table and AWS do not match:")
        print("Table: {}; AWS: {}".format(entries,current_items))

## load_gymchecker()
# Returns the gymchecker object, to play around with in iPython
def load_gymchecker():
    dbp = rel_path("data/gymchecker2.db")
    params = (('ID','INTEGER'),('date','INTEGER'),('day','TEXT'),('time','INTEGER'),('value','INTEGER'))
    return databaseObject(dbp, 'gymchecker', params)

## update_gymchecker()
# Creates the gymchecker table if missing, and updates it
def update_gymchecker():
    gc = load_gymchecker()
    update_from_aws_gymchecker(gc)

## round_time(time_string)
# Converts a time_string to a decimal representation of time, rounded to the
# nearest half-hour.
def round_time(time_string):
    hours, mins = [int(s) for s in time_string.split(":")]
    if mins < 15:
        mins = 0
    elif mins < 45:
        mins = 0.5
    else:
        mins = 0
        hours += 1
    return hours + mins

##### Analysis Functions #######################################################

class date():
    def __init__(self,value):
        type_int = type(1)
        type_str = type("a")
        type_date = type(datetime.date(1,1,1))

        if type(value) not in (type_int, type_str, type_date):
            print("ERROR: Not a valid date type: {} = {}".format(value, type(value)))
            return

        if type(value) == type_date:
            self.value = value
            return

        d_strings = re.findall("(\d{4})-?(\d{2})-?(\d{2})",str(value))[0]
        d_ints = [int(i) for i in d_strings]
        self.value = datetime.date(*d_ints)

    def __int__(self):
        date_string = "".join(re.findall("(\d)",str(self.value)))
        return int(date_string)

    def __str__(self):
        return str(self.value)

class graph_plotter(tk.Frame):

    ##### Standard Data ########################################################

    open_hours = ((13,46),(13,46),(13,46),(13,46),(13,46),(16,46),(16,43)) # Can be exported to separate file?
    open_times = [list(t/2 for t in range(h[0],h[1])) for h in open_hours]
    day_names = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
    day_abbr = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")
    day_index = 0


    ##### Button Functions #####################################################

    def check_escape(self, event):
        if event.keysym == "Escape":
            self.master.quit()
            self.master.destroy()

    def set_day(self, diff):
        self.day_index = (self.day_index + diff) % 7
        self.label_day.configure(text=self.day_abbr[self.day_index])
        self.plot_figure()

    def recalculate(self):
        self.waitscreen_start()
        self.update()
        self.calculate_data()
        self.plot_figure()
        self.waitscreen_stop()
        self.update()

    def hover(self, event):
        if event.inaxes == self.ax:
            self.show_value(event)

    def mouse_leave_plot(self, event):
        self.show_value(None)


    ##### Follow-up Functions ##################################################

    def week_select(self, event):
        widget = event.widget
        index = widget.curselection()[0]
        if self.week_switches[index] == 0:
            self.week_switches[index] = 1
        else:
            self.week_switches[index] = 0
        self.rewrite_weeks(widget)

    def rewrite_weeks(self, widget):
        widget.delete(0,"end")
        for i in range(len(self.week_starts)):
            if self.week_switches[i] == 0:
                widget.insert("end",strikethrough(self.week_starts[i]))
                widget.itemconfig("end", foreground="#999999")
            else:
                widget.insert("end",self.week_starts[i])

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


    ##### Drawing / Positioning ################################################

    def position(self):
        # Base Frames
        self.f1 = tk.Frame(self)
        self.f2 = tk.Frame(self)
        self.f3 = tk.Frame(self)
        self.f4 = tk.Frame(self)

        self.f1.rowconfigure(1,weight=1)
        self.f4.columnconfigure(1,minsize=50)
        self.f2.rowconfigure(0,weight=1)

        self.f1.grid(row=0, column=0, sticky=tk.N+tk.W+tk.S+tk.E)
        self.f2.grid(row=0,column=1)
        self.f3.grid(row=1,column=0)
        self.f4.grid(row=1,column=1)

        # Frame 1
        self.label_select_weeks = tk.Label(master=self.f1,text="Selected Weeks:")
        self.label_select_weeks.grid(row=0, sticky=tk.W)

        self.lb_weeks = tk.Listbox(master=self.f1,selectmode="SINGLE")
        self.lb_weeks.bind('<<ListboxSelect>>',self.week_select)
        self.lb_weeks.grid(row=1, sticky=tk.N+tk.W+tk.S+tk.E)

        for w in self.week_starts:
            self.lb_weeks.insert("end", w)

        # Frame 2
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.f2)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, sticky=tk.N+tk.W+tk.S+tk.E)

        self.plot_figure()

        self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.mpl_connect("axes_leave_event", self.mouse_leave_plot)

        self.label_values = tk.Label(master=self.f2, text="")
        self.label_values.grid(row=1, sticky=tk.W)

        self.label_mousepos = tk.Label(master=self.f2, text="", fg="#777777")
        self.label_mousepos.grid(row=2, sticky=tk.W)

        # Frame 3
        self.button_recalc = tk.Button(master=self.f3, text="Recalculate", \
            command=self.recalculate)
        self.button_recalc.pack()

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
        max_value = 5*(round(arraymax(self.data)/5)+1)
        self.ax.set_ylim([0,max_value])
        self.ax.xaxis.set_ticks(list(range(6,24)))
        self.ax.axhline(y=mean(self.data[i]))
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

    ##### Calculation Functions ################################################

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
        print("Data ranges from {} to {}".format(start_date, end_date))
        temp_date = start_date
        week_starts = []
        while True:
            week_starts.append(str(date(temp_date)))
            temp_date += datetime.timedelta(days=7)
            if temp_date > end_date:
                break
        self.week_starts = week_starts
        self.week_switches = [1 for _ in week_starts]

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


    ##### init function ########################################################

    def __init__(self, master, gc):
        self.gc = gc
        tk.Frame.__init__(self, master)
        master.bind("<KeyPress>", self.check_escape)
        self.get_week_starts()
        self.calculate_data()
        self.position()
        self.set_day(0)


##### main function ############################################################

def main():
    if (any(x in ("--update","-u") for x in sys.argv)):
            # Update gymchecker
            update_gymchecker()

    gc = load_gymchecker()

    root=tk.Tk()
    graph_plotter(root, gc)
    root.mainloop()

if __name__=="__main__":
    main()
