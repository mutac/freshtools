import itertools
import collections
from peewee import *
from decimal import Decimal


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


def currency(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'
    """

    value = Decimal(value)
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))