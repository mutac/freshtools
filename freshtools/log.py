from freshtools.models import LogDestination, TaskLog, TimeEntry


def add_destination(destination):
    LogDestination.create(destination=destination)


def remove_destination(destination):
    LogDestination.delete(
        LogDestination.get(destination=destination)
    )


def list_destinations(print_func):
    for dest in  LogDestination.select():
        print_func(dest.destination)


def log_entries(time_entries, destination):
    for entry in time_entries:
        TaskLog.create(time_entry=entry, log_destination=destination)


def time_entries(client, start_date, end_date):
    qs = TimeEntry.select()

    if client is not None:
        qs = qs.where(
            TimeEntry.client == client
        )

    if start_date is not None:
        qs = qs.where(
            TimeEntry.created_at >= start_date
        )

    if end_date is not None:
        qs = qs.where(
            TimeEntry.created_at <= end_date
        )

    return qs