from log import get_logger
from models import ALL_MODELS
from util import model_dependency_order, create_tables, drop_tables


logger = get_logger()


def initialize():
    models = model_dependency_order(ALL_MODELS)
    drop_tables(models)
    create_tables(models)


def list():
    for model in ALL_MODELS:
        if model.table_exists():
            logger.info(model.__name__)


def status():
    for model in ALL_MODELS:
        logger.info('%s: %s' % (
            model.__name__,
            '%d records' % (model.select().count()) if model.table_exists else 'empty'
        ))


def pull(api, models):
    dep_order = model_dependency_order(models)

    for model in dep_order:
        logger.info('Caching: %s' % model.__name__)
        model.pull(api)
        logger.info('   Records: %s' % model.select().count())