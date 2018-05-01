import os
import collections
from peewee import *
from refresh2.util import memoize
from models import Account, Business, Client, Project, Task, TimeEntry
from exceptions import *
from util import head, coalate, currency


class Summary(object):
    def __init__(self):
        pass

    def query_set(self):
        return None

    def format_title(self, row):
        raise ImproperlyConfiguredException()

    def format_row(self, row):
        raise ImproperlyConfiguredException()

    def print_report(self, printer):
        for row in self.query_set():
            header = self.format_title(row).encode('utf8', 'replace')
            bars = '-' * len(header)

            printer(bars)
            printer(header)
            printer(bars)
            printer(self.format_row(row).encode('utf8', 'replace'))
            printer('')


class TaskTimeEntrySummaryMixin(object):
    aggregate_by = ()

    def query_set(self):
        qs = TimeEntry.select(
            TimeEntry,
            Task,
            fn.Sum(TimeEntry.duration).alias('total_time'),
            fn.Min(TimeEntry.started_at).alias('first_date'),
            fn.Max(TimeEntry.started_at).alias('last_date')
        ).join(
            Task, JOIN_LEFT_OUTER
        ).group_by(
            *self.aggregate_by
        ).order_by(
            SQL('last_date')
        )

        if self.window.client is not None:
            qs = qs.where(
                TimeEntry.client == self.window.client
            )

        if self.window.start_date is not None:
            qs = qs.where(
                TimeEntry.started_at >= self.window.start_date
            )

        if self.window.end_date is not None:
            qs = qs.where(
                TimeEntry.started_at <= self.window.end_date
            )

        return qs


class TasksByClient(TaskTimeEntrySummaryMixin, Summary):
    aggregate_by = (
        Task.id,
        TimeEntry.client
    )

    def __init__(self, time_entry_window=None):
        self.window = time_entry_window

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


class DaysByClientProjectTask(TaskTimeEntrySummaryMixin, Summary):
    aggregate_by = (
        Task.id,
        TimeEntry.project,
        TimeEntry.client,
        TimeEntry.started_at_date,
    )

    def __init__(self, time_entry_window=None):
        self.window = time_entry_window

    def query_set(self):
        tasks = super(DaysByClientProjectTask, self).query_set()

        day_client_project_tasks = coalate(
            tasks, by=['started_at_date', 'client', 'project'])
        return day_client_project_tasks.values()

    def format_title(self, row):
        return str(head(head(head(row))).started_at_date)

    def format_row(self, row):
        formatted = []

        for client_project_tasks in row.values():
            task = head(head(head(client_project_tasks)))
            formatted.append('  Client: %s' % task.client.organization)

            for project_tasks in client_project_tasks.values():
                task = head(head(project_tasks))
                formatted.append('    Project: %s' % task.project.title)

                for task in project_tasks:
                    formatted.append("""      Task: %s
      Total Time: %0.2f hours
      Billed: %s
""" % (
                        task.task.name if task.task else '<UNCATEGORIZED>',
                        task.total_time / 60.0 / 60.0,
                        'Yes' if task.billed else 'No'))

        return os.linesep.join(formatted)


class TimePeriodByClientProject(TaskTimeEntrySummaryMixin, Summary):
    @property
    def aggregate_by(self):
        return (
            self.time_period_field,
            TimeEntry.client,
            TimeEntry.project,
        )

    def query_set(self):
        tasks = super(TimePeriodByClientProject, self).query_set()

        aggregate_by_names = map(lambda field: field.name, self.aggregate_by)

        week_client_project_tasks = coalate(
            tasks, by=aggregate_by_names)
        return week_client_project_tasks.values()

    def format_row(self, row):
        formatted = []

        for client_project_by_time_period in row.values():
            time_period = head(head(head(client_project_by_time_period)))
            formatted.append('  Client: %s' % time_period.client.organization)

            for project_by_time_period in client_project_by_time_period.values():
                time_period = head(head(project_by_time_period))
                hours = time_period.total_time / 60.0 / 60.0
                formatted.append("""    Project: %s
      Total Time: %0.2f hours
      Invoice Amount: %s
""" % (
                    time_period.project.title,
                    hours,
                    currency(time_period.project.hourly_rate * hours, curr='$')))

        return os.linesep.join(formatted)


class WeeksByClientProject(TimePeriodByClientProject, Summary):
    time_period_field = TimeEntry.started_at_week_ending_date

    def __init__(self, time_entry_window=None):
        self.window = time_entry_window.aligned_to_week_boundaries()

    def format_title(self, row):
        return 'Week Ending: ' + str(head(head(head(row))).started_at_week_ending_date)


class MonthsByClientProject(TimePeriodByClientProject, Summary):
    time_period_field = TimeEntry.started_at_month_ending_date

    def __init__(self, time_entry_window=None):
        self.window = time_entry_window.aligned_to_month_boundaries()

    def format_title(self, row):
        return 'Month Ending: ' + str(head(head(head(row))).started_at_month_ending_date)


class YearsByClientProject(TimePeriodByClientProject, Summary):
    time_period_field = TimeEntry.started_at_year_ending_date

    def __init__(self, time_entry_window=None):
        self.window = time_entry_window.aligned_to_year_boundaries()

    def format_title(self, row):
        return 'Year Ending: ' + str(head(head(head(row))).started_at_year_ending_date)