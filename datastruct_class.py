# Input all data into timeData objects
# Calculate daily averages
# Calculate weekly averages
# Calculate day-offset for each timeData
# Calculate week-offset for each timeData
# Calculate week-offset for day average
import re

test_data = [{
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

a = {
    1: 2,
    3: 4,
    5: 6
}

class dayObject():
    def __init__(self,data):
        self.id = data["id"]
        self.day = data["day"]
        self.date = data["date"]
        self.data = data["data"]
        self.average = self.calculate_average()

    def calculate_average(self):
        total = 0
        count = 0
        for entry in self.data.items():
            if entry[1] != None:
                total += entry[1]
                count += 1
        return total / count

class dataObject():

    time_dict = {t: None for t in map(lambda x: x/2, range(48))}

    def __init__(self,data):
        self.days = []
        for _, entry in self.format_data(data).items():
            self.days.append(dayObject(entry))

    def format_data(self,data_object):
        data = {}
        for entry in data_object:
            e_date = entry["date"]
            e_time = self.round_time(entry["time"])
            e_id = entry["ID"]
            e_day = entry["day"]
            e_value = int(re.findall("(\d+)%",entry["value"])[0])

            if e_day == "Saturday":
                if not (8 <= e_time < 22.5):
                    continue
            elif e_day == "Sunday":
                if not (8 <= e_time < 21):
                    continue
            else:
                if not (6.5 <= e_time < 22.5):
                    continue

            try:
                data[e_date]["data"][e_time] = e_value
                data[e_date]["id"] = min(data[e_date]["id"],entry["ID"])
            except KeyError:
                data[e_date] = {
                    "data": self.time_dict,
                    "day": e_day,
                    "id": e_id,
                    "date": e_date
                }
                data[e_date]["data"][e_time] = e_value
        return data

    def round_time(self,time_string):
        hours, mins = [int(s) for s in time_string.split(":")]
        if mins < 15:
            mins = 0
        elif mins < 45:
            mins = 0.5
        else:
            mins = 0
            hours += 1
        return hours + mins

d = dataObject(test_data)
print(d.days[0].data[11])

class weekData():
    pass
    # weeknum
    # year
    # data # An array of dayData objects
    # average # Averaged over all days



# Will need a reference list - Do I keep days separate, and just create a list
# for them? Or do I stick with weeks, and create a function that will be able to
# look up a certain date?
