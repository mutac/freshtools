import itertools
import collections
import datetime
from dateutil.parser import parse as dateutil_parse_date
from dateutil import tz
from peewee import *


def head(v):
    if isinstance(v, list):
        return v[0]
    elif isinstance(v, dict):
        return v.itervalues().next()
    elif isinstance(v, basestring):
        return v[0]
    else:
        return v


def lookahead(iterable):
    it = iter(iterable)
    last = next(it)
    for val in it:
        yield last, True
        last = val
    yield last, False


def coalate(rows, by=[]):
    if not by:
        return rows

    coalated = collections.OrderedDict()

    for row in rows:
        _coalated = coalated

        for key, more in lookahead(by):
            key_value = getattr(row, key)

            if key_value not in _coalated:
                _coalated[key_value] = [] if not more else collections.OrderedDict()

            _coalated = _coalated[key_value]

        _coalated.append(row)

    return coalated


def get_immediate_dependencies(model):
    dependencies = []

    for field in model._meta.fields.values():
        if type(field) is ForeignKeyField:
            dependencies.append(field.rel_model)

    return dependencies


def model_dependency_order(models):
    def topo_sort(models, visited):
        ordered = []

        for model in models:
            if not model in visited:
                visited.add(model)

                ordered = ordered + topo_sort(
                    get_immediate_dependencies(model),
                    visited
                )
                ordered.append(model)

        return ordered

    return topo_sort(models, set())


def create_tables(models):
    for model in models:
        if not model.table_exists():
            model.create_table()


def drop_tables(models):
    for model in models:
        if model.table_exists():
            model.drop_table()


def parse_datetime(date):
    if type(date) is datetime.date:
        return datetime.datetime.combine(date, datetime.datetime.min.time())

    if type(date) is datetime.datetime:
        return date

    return dateutil_parse_date(date)


def local_from_utc_datetime(date):
    date = parse_datetime(date)
    return date.astimezone(tz.tzlocal())


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


def todays_date():
    return beginning_of_day(datetime.date.today())


def n_days_ago_date(days_ago):
    return beginning_of_day(todays_date() - datetime.timedelta(days=days_ago))


def this_weeks_date():
    return beginning_of_day(week_ending_datetime(todays_date()))


def n_weeks_ago_date(weeks_ago):
    days_ago = weeks_ago * 7
    return beginning_of_day(week_ending_datetime(n_days_ago_date(days_ago)))
