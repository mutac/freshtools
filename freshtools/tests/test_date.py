import pytest
from dateutil.parser import parse as dateutil_parse_date

from freshtools.date import *


def test_beginning_of_day():
    date = dateutil_parse_date('2/1/2018')
    assert beginning_of_day(date) == dateutil_parse_date('2018-02-01 00:00:00')


def test_ending_of_day():
    date = dateutil_parse_date('2/2/2018')
    assert ending_of_day(date) == dateutil_parse_date('2018-02-02 23:59:59.999999')


def test_month_starting_and_ending_datetime():
    date = '2/15/2018'
    expected_start = '2/1/2018'
    expected_end = '2/28/2018'

    start, end = month_starting_and_ending_datetime(date)
    assert start == beginning_of_day(expected_start)
    assert end == ending_of_day(expected_end)


def test_year_starting_and_ending_datetime():
    date = '2/20/2018'
    expected_start = '1/1/2018'
    expected_end = '12/31/2018'

    start, end = year_starting_and_ending_datetime(date)
    assert start == beginning_of_day(expected_start)
    assert end == ending_of_day(expected_end)