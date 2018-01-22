import itertools
import collections
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
