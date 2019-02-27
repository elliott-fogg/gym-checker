import os, decimal, datetime, re, json

##### Preset Variables #########################################################

## A dictionary for converting from Python types to SQLite Types
sql_type = {
    'str' : 'TEXT',
    'int' : 'INTEGER',
    'float' : 'REAL',
    'bytes' : 'BLOB',
    'NoneType' : 'NULL'
    }

gc_params = (
    ('ID','INTEGER'),
    ('date','INTEGER'),
    ('day','TEXT'),
    ('time','INTEGER'),
    ('value','INTEGER')
)

db_name = "gymchecker2.db"

##### global variables #########################################################

g_root_folder = ""
g_quiet = True

def set_folder_paths(root_folder):
    global g_root_folder
    g_root_folder = root_folder

def data(rpath):
    return g_root_folder + "/data/" + rpath

def classes(rpath):
    return g_root_folder + "/classes/" + rpath

def tests(rpath):
    return g_root_folder + "/tests/" + rpath

def rel(rpath):
    return g_root_folder + "/" + rpath

def set_quiet(b):
    if b == True:
        g_quiet = True
    else:
        g_quiet = False

def qprint(message):
    if g_quiet == False:
        print(message)


##### Additional Classes #######################################################

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

class mouseControl():
    def __init__(self, widget, delay=300):
        self.double_click_flag = False
        self.button_released_flag = False
        self.widget = widget
        self.widget.bind('<Button-1>', self.clicked)
        self.widget.bind('<Double-1>', self.double_click)
        self.widget.bind('<ButtonRelease-1>', self.button_released)
        self.widget.bind('<B1-Motion>', self.moved)
        self.delay = delay

    def clicked(self, event):
        self.double_click_flag, self.button_released_flag = False, False
        self.widget.after(self.delay, self.action, event)

    def double_click(self, event):
        self.double_click_flag = True

    def button_released(self, event):
        self.button_released_flag = True

    def moved(self, event):
        pass

    def action(self, event):
        if self.button_released_flag:
            if self.double_click_flag:
                print("double mouse click event")
            else:
                print("single mouse click event")


##### Additional Functions #####################################################

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

def rel_path(path):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dirname + "/" + path

def strikethrough(text):
    return '\u0336'.join(text) + '\u0336'
