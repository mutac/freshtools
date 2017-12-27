import os
import collections
from peewee import *
from refresh2.util import memoize
from models import Account, Business, Client, Project, Task, TimeEntry
from exceptions import *
from util import week_starting_datetime, week_ending_datetime

class Summary(object):
    def __init__(self):
        pass

    def query_set(self):
        return None

    def format_title(self, row):
        raise ImproperlyConfiguredException()

    def format_row(self, row):
        raise ImproperlyConfiguredException()

    def print_report(self):
        for row in self.query_set():
            header = self.format_title(row).encode('utf8', 'replace')
            bars = '-' * len(header)

            print bars
            print header
            print bars
            print self.format_row(row).encode('utf8', 'replace')
            print ''


class TaskTimeEntrySummaryMixin(object):
    aggregate_by = ()

    def query_set(self):
        qs = TimeEntry.select(
            TimeEntry,
            Task,
            fn.Sum(TimeEntry.duration).alias('total_time'),
            fn.Min(TimeEntry.created_at).alias('first_date'),
            fn.Max(TimeEntry.created_at).alias('last_date')
        ).join(
            Task
        ).group_by(
            *self.aggregate_by
        ).order_by(
            SQL('last_date')
        )

        if self.client is not None:
            qs = qs.where(
                TimeEntry.client == self.client
            )

        if self.start_date is not None:
            qs = qs.where(
                TimeEntry.created_at >= self.start_date
            )

        if self.end_date is not None:
            qs = qs.where(
                TimeEntry.created_at <= self.end_date
            )

        return qs


class TasksByClient(TaskTimeEntrySummaryMixin, Summary):
    aggregate_by = (
        Task.id,
        TimeEntry.client
    )

    def __init__(self, client=None, start_date=None, end_date=None):
        self.client = client
        self.start_date = start_date
        self.end_date = end_date

    def format_title(self, row):
        return row.task.name

    def format_row(self, row):
        return """Client: %s
Total Time: %0.2f hours
First Entered: %s
Last Entered: %s""" % (
            row.client.organization,
            row.total_time / 60.0 / 60.0,
            row.first_date,
            row.last_date)


class DaysByClientTask(TaskTimeEntrySummaryMixin, Summary):
    aggregate_by = (
        Task.id,
        TimeEntry.created_at_date,
        TimeEntry.client
    )

    def __init__(self, client=None, start_date=None, end_date=None):
        self.client = client
        self.start_date = start_date
        self.end_date = end_date

    def query_set(self):
        tasks = super(DaysByClientTask, self).query_set()

        #
        # Builds a dictionary, of dictionaries, of lists...
        #
        # record[day][client][taskN]
        #

        day_client_tasks = collections.OrderedDict()

        for task in tasks:
            if task.created_at_date not in day_client_tasks:
                day_client_tasks[task.created_at_date] = collections.OrderedDict()

            if task.client not in day_client_tasks[task.created_at_date]:
                day_client_tasks[task.created_at_date][task.client] = []

            day_client_tasks[task.created_at_date][task.client].append(task)

        return day_client_tasks.values()

    def format_title(self, row):
        return str(row.itervalues().next()[0].created_at_date)

    def format_row(self, row):
        formatted = []

        for client_tasks in row.values():
            formatted.append('  Client: %s' %
                             client_tasks[0].client.organization)

            for task in client_tasks:
                formatted.append("""    Task: %s
    Total Time: %0.2f hours
""" % (
                    task.task.name,
                    task.total_time / 60.0 / 60.0))

        return os.linesep.join(formatted)


class WeeksByClientProject(TaskTimeEntrySummaryMixin, Summary):
    aggregate_by = (
        TimeEntry.client,
        TimeEntry.project,
        TimeEntry.created_at_week_ending_date
    )

    def __init__(self, client=None, start_date=None, end_date=None):
        self.client = client

        # Expand search ROI along week boundaries
        self.start_date = week_starting_datetime(start_date)
        self.end_date = week_ending_datetime(end_date)

    def format_title(self, row):
        return row.project.title

    def format_row(self, row):
        return """Client: %s
Total Time: %0.2f hours
Week Ending: %s""" % (
            row.client.organization,
            row.total_time / 60.0 / 60.0,
            row.created_at_week_ending_date)