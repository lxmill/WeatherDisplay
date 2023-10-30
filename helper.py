def hh_mm(time_struct):
    """
    Given a time.struct_time, return a string as HH:MM 24-hour style.
    This is ONLY for 'clock time'
    """
    hour_string = "{0:0>2}".format(time_struct.tm_hour)
    return hour_string + ":" + "{0:0>2}".format(time_struct.tm_min)


def date(time_struct):
    """
    Given a time.struct_time, return a string as 30 Jun style.
    """
    months_pt = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]

    day_str = "{0:0>2}".format(time_struct.tm_mday)
    month_str = months_pt[int(time_struct.tm_mon) - 1]

    return f"{month_str} {day_str}"
