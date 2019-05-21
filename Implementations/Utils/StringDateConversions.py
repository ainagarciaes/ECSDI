import datetime

def dateToString(d):
    return d.strftime("%Y-%m-%d")

def stringToDate(s):
    d = datetime.datetime.strptime(str(s), "%Y-%m-%d") 
    return d