from peewee import DoesNotExist
from log import get_logger
from models import ALL_MODELS, db, MetaData
from util import model_dependency_order, create_tables, drop_tables


logger = get_logger()


def initialize():
    models = model_dependency_order(ALL_MODELS)
    drop_tables(models)
    create_tables(models)

    MetaData.reset()


def status():
    for model in ALL_MODELS:
        logger.info('%s: %s' % (
            model.__name__,
            '%d records.  (Last updated %s)' % (
                model.select().wrapped_count(),
                MetaData.get_last_pulled_time(model)
            ) if model.table_exists() else ('empty', 'never')
        ))


def show(models):
    indent = 2
    print_func = lambda s: logger.info(' ' * indent + s)

    for model in models:
        logger.info('%ss' % model.__name__)

        for row in model.select():
            try:
                row.show(print_func)
                logger.info('')
            except DoesNotExist:
                pass


def pull(api, models):
    dep_order = model_dependency_order(models)

    for model in dep_order:
        with db().atomic():
            if not model.table_exists():
                create_tables([model])

            logger.info('Caching: %s' % model.__name__)
            model.pull(api)
            logger.info('   Records: %s' % model.select().count())

            MetaData.update_last_pulled_time(model)