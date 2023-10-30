from pymongo import MongoClient
from datetime import datetime

client = MongoClient(port= 27017)


filier = ['IDSD2']
day = datetime.today().strftime('%A')
timeTablle = dict()
db = client.get_database('timetable')
tableresults = db.timetable.find({'filiere':{"$in":filier}},{'filiere':0,"_id":0})
time = "08:30-12"
prof = 'GUEZZAZ Azzdine'
for t in tableresults:
    timeTablle = dict(t)
for key in timeTablle:
        if key == day:
            print(timeTablle[key])
            for value in timeTablle[key]:
                if (time == value) is True:
                    if timeTablle[key][value][1] != prof:
                        print('hi')

                    
