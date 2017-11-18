import itertools
import datetime
from dateutil.parser import parse as dateutil_parse_date
from peewee import *


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


def parse_date(date):
    if type(date) is datetime.date:
        return date

    return dateutil_parse_date(date)