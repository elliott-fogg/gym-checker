import os, sqlite3, re, json, boto3, decimal, shutil
from boto3.dynamodb.conditions import Key, Attr

##### Utility Functions / Dictionaries #########################################

oseu = os.path.expanduser

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

## Get the SQLite type of a variable
def get_type(arg):
    value = str(type(arg))[8:-2]
    try:
        return sql_type[value]
    except:
        return "TEXT"

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

            param_type_array = []
            for key in self.param_order:
                if self.params[key] != get_type(entry[key]):
                    param_type_array.append( (key,entry[key],get_type(entry[key]),self.params[key]) )
            if param_type_array != []:
                print("Entry {} has values of the wrong type:")
                for p in param_type_array:
                    print("\t{}={} ('{}', should be '{}')".format(*p))
                    print(entry)
                continue

            # If we've reached here, entry has passed all checks
            valid_entries.append(entry)

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

    def get_uniques(self,column_name):
        r = self.x("SELECT DISTINCT {} FROM {} ORDER BY {}".format(\
            column_name, self.table, column_name))

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
    print(json.dumps(response_data, indent=2))
    print("")

    # Insert results into table
    dbObject.insert_data(results)

    # Check the number of entries in the table
    entries = dbObject.count_entries()
    print("{} entries in table.".format(entries))

    backup(dbObject.file_path)

## load_gymchecker()
# Returns the gymchecker object, to play around with in iPython
def load_gymchecker():
    dbp = rel_path("data/gymchecker.db")
    params = (('ID','INTEGER'),('date','TEXT'),('day','TEXT'),('time','TEXT'),('value','TEXT'))
    return databaseObject(dbp, 'gymchecker', params)

## setup_gymchecker()
# Creates the gymchecker table if missing, and updates it
def setup_gymchecker():
    gc = load_gymchecker()
    update_from_aws_gymchecker(gc)
