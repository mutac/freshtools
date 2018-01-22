from models import Client, get_the_one_or_fail
from date import week_ending_datetime, week_starting_datetime

class TimeEntryWindow(object):
    def __init__(self, client=None, start_date=None, end_date=None):
        self.start_date = start_date
        self.end_date = end_date

        if client:
            self.client = get_the_one_or_fail(Client, client=client)
        else:
            self.client = None

    def aligned_to_week_boundaries(self):
        return TimeEntryWindow(
            self.client,
            week_starting_datetime(self.start_date),
            week_ending_datetime(self.end_date)
        )


def time_entry_window(client=None, start_date=None, end_date=None):
    return TimeEntryWindow(client, start_date, end_date)