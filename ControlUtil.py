import pytz, datetime
from tkinter import *

def addControl(mainArr, *controls):
    for c in controls:
        mainArr.append(c)

def setControlState(controls, state):
    for c in controls:
        c.config(state=state)

def clearTextBoxes(tboxes):
    for t in tboxes:
        t.delete(0, END)

def entriesHaveValues(tboxes):
    result = True

    for t in tboxes:
        result = eval('len(t.get().strip()) > 0 and result')

    return result


def getUtcTime(localdate, localtime, timezone):

    dtformat = "%Y-%m-%d %H:%M"
    localTimezone = pytz.timezone(timezone)
    naive = datetime.datetime.strptime("{0} {1}".format(localdate,localtime), dtformat)

    local_dt = localTimezone.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)

    return utc_dt.strftime(dtformat)

def getToday(format):
    return datetime.datetime.now().strftime(format)
