from models import Client, get_the_one_or_fail
from date import (week_starting_datetime, week_ending_datetime,
    month_starting_datetime, month_ending_datetime,
    year_starting_datetime, year_ending_datetime)

class TimeEntryWindow(object):
    def __init__(self, client=None, start_date=None, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.client = None

        if client:
            if isinstance(client, basestring):
                self.client = get_the_one_or_fail(Client, client=client)
            else:
                self.client = client

    def aligned_to_week_boundaries(self):
        return TimeEntryWindow(
            self.client,
            week_starting_datetime(self.start_date),
            week_ending_datetime(self.end_date)
        )

    def aligned_to_month_boundaries(self):
        return TimeEntryWindow(
            self.client,
            month_starting_datetime(self.start_date),
            month_ending_datetime(self.end_date)
        )

    def aligned_to_year_boundaries(self):
        return TimeEntryWindow(
            self.client,
            year_starting_datetime(self.start_date),
            year_ending_datetime(self.end_date)
        )


def time_entry_window(client=None, start_date=None, end_date=None):
    return TimeEntryWindow(client, start_date, end_date)