import click
from util import parse_datetime

class ParsedParameter(click.ParamType):
    name = 'date'

    def __init__(self, parser):
        self.parser = parser

    def convert(self, value, param, ctx):
        if value is None:
            return value

        try:
            return self.parser(value)
        except ValueError as ex:
            self.fail('%s' % ex, param, ctx)


class DateTimeParameter(ParsedParameter):
    def __init__(self):
        super(DateTimeParameter, self).__init__(parse_datetime)