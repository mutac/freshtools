import datetime
from dateutil import tz
from dateutil.parser import parse as dateutil_parse_date
from dateutil.relativedelta import relativedelta

def parse_datetime(date):
    if type(date) is datetime.date:
        return datetime.datetime.combine(date, datetime.datetime.min.time())

    if type(date) is datetime.datetime:
        return date

    return dateutil_parse_date(date)


def local_from_utc_datetime(date):
    date = parse_datetime(date)
    local = date.astimezone(tz.tzlocal())
    return local


def beginning_of_day(date):
    date = parse_datetime(date)
    return datetime.datetime.combine(date.date(), datetime.datetime.min.time())


def ending_of_day(date):
    date = parse_datetime(date)
    return datetime.datetime.combine(date.date(), datetime.datetime.max.time())


def day_starting_and_ending_datetime(date):
    if date is not None:
        date = parse_datetime(date)

        return (beginning_of_day(date), ending_of_day(date))
    else:
        return (None, None)


def week_starting_and_ending_datetime(date):
    if date is not None:
        date = parse_datetime(date)

        start = beginning_of_day(date - datetime.timedelta(days=date.weekday()))
        end = ending_of_day(start + datetime.timedelta(days=6))

        return (start, end)
    else:
        return (None, None)


def week_starting_datetime(date):
    start, _ = week_starting_and_ending_datetime(date)
    return start


def week_ending_datetime(date):
    _, end = week_starting_and_ending_datetime(date)
    return end


def month_starting_and_ending_datetime(date):
    if date is not None:
        date = parse_datetime(date)

        year_delta, month = divmod(date.month - 1, 12)
        first_day_of_month = datetime.date(date.year + year_delta, month + 1, 1)
        start = beginning_of_day(first_day_of_month)
        end = ending_of_day(start + relativedelta(months=1, days=-1))

        return (start, end)
    else:
        return (None, None)


def month_starting_datetime(date):
    start, _ = month_starting_and_ending_datetime(date)
    return start


def month_ending_datetime(date):
    _, end = month_starting_and_ending_datetime(date)
    return end


def year_starting_and_ending_datetime(date):
    if date is not None:
        date = parse_datetime(date)

        start = beginning_of_day(date.replace(month=1, day=1))
        end = ending_of_day(date.replace(month=12, day=31))

        return (start, end)
    else:
        return (None, None)


def year_starting_datetime(date):
    start, _ = year_starting_and_ending_datetime(date)
    return start


def year_ending_datetime(date):
    _, end = year_starting_and_ending_datetime(date)
    return end


def todays_date():
    return beginning_of_day(datetime.date.today())


def n_days_ago_date(days_ago):
    return beginning_of_day(todays_date() - datetime.timedelta(days=days_ago))


def this_weeks_date():
    return beginning_of_day(week_ending_datetime(todays_date()))


def n_weeks_ago_date(weeks_ago):
    weeks_ago_date = todays_date() - datetime.timedelta(weeks=weeks_ago)
    return beginning_of_day(week_ending_datetime(weeks_ago_date))


def this_months_date():
    return beginning_of_day(month_ending_datetime(todays_date()))


def n_months_ago_date(months_ago):
    months_ago_date = todays_date() - relativedelta(months=months_ago)
    return beginning_of_day(month_ending_datetime(months_ago_date))


def this_years_date():
    return beginning_of_day(year_ending_datetime(todays_date()))


def n_years_ago_date(years_ago):
    years_ago_date = todays_date() - relativedelta(years=years_ago)
    return beginning_of_day(year_ending_datetime(years_ago_date))