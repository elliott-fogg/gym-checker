##### Test Suite ###############################################################

import database_class2 as dbc
import json, os, sqlite3, boto3, decimal, shutil

## Test Data that is in the correct format
valid_data = [{
    "date": "2018-12-07",
    "time": "10:30",
    "ID": 1544178641,
    "day": "Friday",
    "value": "32%"
    },
    {
    "date": "2018-12-07",
    "time": "11:00",
    "ID": 1544180441,
    "day": "Friday",
    "value": "26%"
    }]

## Test Data that is incorrectly formatted
faulty_data = [
    "pinnochio",
    {
        "date": 20181206,
        "time": "10:30",
        "ID": "15234",
        "faulty_label": "something",
        "values": 64
    }]

## Test Data that only has a single entry
single_data = [
    {
    "date": "2018-12-07",
    "time": "10:30",
    "ID": 1544178641,
    "day": "Friday",
    "value": "32%"
    }]

## Test the data conversion in the gymchecker database
data = json.load(open(dbc.rel_path("data/sample_data.txt"),"r"))
test_data = data["Items"]
gc = dbc.load_gymchecker()
gc.insert_data(test_data)
gc.drop_table("gymchecker")

## run_test()
# Tests the databaseObject() class on the 3 sets of data above. Works on a test
# table, and drops it afterwards.
db_path = dbc.rel_path("data/gymchecker.db")
params = (('ID','INTEGER'),('date','TEXT'),('day','TEXT'),('time','TEXT'),('value','TEXT'))
test = dbc.databaseObject(db_path, 'test', params)

print("\nTesting Valid Data:")
test.insert_data(valid_data)
print("\nTesting Faulty Data:")
test.insert_data(faulty_data)
print("\nTesting Single Data:")
test.insert_data(single_data)

print("\nQuery results:")
print(sorted(test.query("time='11' AND day='Friday'"),key=lambda x:x[0]))

print("\nMax ID: {}".format(\
    test.x("SELECT MAX(ID) FROM {}".format(test.table))[0][0]))
test.drop_table("test")
