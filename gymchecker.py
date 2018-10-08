#!/usr/bin/python3.6

import requests, re, time, datetime, os

dataPath = '/home/elfest2/dataFile.txt'
errorPath = '/home/elfest2/errorFile.txt'

def checkGymOcc():
    r = requests.get('https://www.st-andrews.ac.uk/sport/')
    return returnObject(r)

def logError(errorPath,r):
    if os.path.isfile(errorPath):
        f = open(errorPath,"a")
    else:
        f = open(errorPath,"w+")
    f.write(r.value)
    f.write("\n")
    f.close()

def createDataFile(dataPath):
  f = open(dataPath,"w+")
  text = "Gym Occupancy Over Time:\n"
  text += "Date\tDay\tTime\tOccupancy\n"
  f.write(text)
  f.close()

def appendData(dataPath,timeObject,returnObject):
    if not os.path.isfile(dataPath):
        createDataFile(dataPath)
    date = timeObject.date
    day = timeObject.day
    t = timeObject.time
    occupancy = returnObject.value
    text = "{}\t{}\t{}\t{}\n".format(date,day,t,occupancy)
    f = open(dataPath,"a")
    f.write(text)
    f.close()

def testloop():
    r = checkGymOcc()
    if not r.success:
        print(r.value)
    else:
        print("Gym Occupancy: {}%".format(r.value))

def mainloop():
    while True:
        mainBlock()
        time.sleep(60*30) # Take a reading every 30 minutes

def mainBlock():
    r = checkGymOcc()
    t = timeObject()
    if r.success:
        appendData(dataPath,t.date,t.day,t.time,r.value)
    else:
        logError(errorPath,r)

class returnObject():
    success = False
    value = None

    def __init__(self,r):
        if r.status_code == 200:
            if len(r.text) > 0:
                self.success = True
                self.value = re.findall('Occupancy: (\d\d?)%',r.text)[0]
            else:
                self.success = False
                self.value = "No text"
        else:
            self.success = False
            self.value = "Failure: ErrorCode({})".format(r.status_code)

class timeObject():
    def __init__(self):
        n = datetime.datetime.now()
        self.date = n.strftime("%Y-%m-%d")
        self.date = n.strftime("%A")
        self.time = n.strftime("%H:%M")

if __name__ == "__main__":
    mainBlock()
