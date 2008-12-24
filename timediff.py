#!/usr/bin/python

import re

from datetime import datetime, timedelta


def extract(td):
    """ Convert the timedelta into a dict of years, months, weeks, days, hours, minutes, seconds. """
    DAYS = td.days
    years = DAYS / 365
    DAYS -= years * 365
    months = DAYS / 30
    DAYS -= months * 30
    weeks = DAYS / 7
    DAYS -= weeks * 7
    days = DAYS

    SECONDS = td.seconds
    hours = SECONDS / 3600
    SECONDS -= hours * 3600
    minutes = SECONDS / 60
    SECONDS -= minutes * 60
    seconds = SECONDS

    return {
        'years' : years,
        'months' : months,
        'weeks' : weeks,
        'days' : days,
        'hours' : hours,
        'minutes' : minutes,
        'seconds' : seconds,
    }


def num_unit_string(num, unit):
    if num == 0:
        return ''
    if num == 1:
        return "1 %s" % ( re.sub('s$', '', unit) )
    return "%d %s" % ( num, unit )

unit_order = ['years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds']
num_units = len(unit_order)

def display(tde):
    start_index = 0
    for i in range(0, num_units):
        if tde[unit_order[i]] > 0:
            start_index = i
            break

    display_string = num_unit_string(tde[unit_order[start_index]], unit_order[start_index])

    if start_index + 1 < num_units:
        ss = num_unit_string(tde[unit_order[start_index+1]], unit_order[start_index+1])
        if ss != '':
            display_string += ', %s' % ( ss )

    return display_string

def show(td):
    return display(extract(td))

######################################################################
# Main.
if __name__ == '__main__':
    import sys

    expression = sys.argv[1]
    supplied_datetime = datetime.strptime(expression, "%Y-%m-%d %H:%M:%S")
    print show(datetime.now() - supplied_datetime) + " ago."

