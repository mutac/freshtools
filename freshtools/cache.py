from peewee import DoesNotExist
from console import get_logger
from models import ALL_MODELS, db, MetaData
from util import model_dependency_order, create_tables, drop_tables


logger = get_logger()


def exists():
    return MetaData.table_exists()


def initialize():
    models = model_dependency_order(ALL_MODELS)
    drop_tables(models)
    create_tables(models)

    MetaData.reset()


def status():
    for model in ALL_MODELS:

        last_pulled = MetaData.get_last_pulled_time(model)

        info = '%s' % model.select().wrapped_count()
        if last_pulled is not None:
            info += ' (last updated %s)' % last_pulled

        logger.info('%s: %s' % (model.__name__, info))


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

            if hasattr(model, 'pull'):
                logger.info('Caching: %s' % model.__name__)
                model.pull(api)
                logger.info('   Records: %s' % model.select().count())

                MetaData.update_last_pulled_time(model)