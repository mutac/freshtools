from peewee import *
from refresh2.util import memoize, classproperty
from exceptions import *
from util import parse_date


@memoize
def db():
    return SqliteDatabase('.freshtools.db')


class BaseModel(Model):
    @classproperty
    def table_name(cls):
        return cls._meta.db_table

    @classmethod
    def pull(cls, api):
        raise ImproperlyConfiguredException()

    @classmethod
    def insert(cls, data):
        with db().atomic():
            if len(data) > 0:
                cls.insert_many(data).execute()

    @classmethod
    def upsert(cls, data):
        with db().atomic():
            if len(data) > 0:
                return cls.insert_many(data).on_conflict('REPLACE').execute()
            else:
                return 0

    class Meta:
        database = db()


class Account(BaseModel):
    id = CharField(unique=True, primary_key=True)

    @classmethod
    def pull(cls, api):
        accounts = []

        for business in api.businesses():
            account = business.account()
            accounts.append({
                'id': account.info['id']
            })

        cls.upsert(accounts)


class Business(BaseModel):
    id = IntegerField(primary_key=True)
    account = ForeignKeyField(Account)
    name = CharField(default='')

    @classmethod
    def pull(cls, api):
        businesses = []

        for business in api.businesses():
            businesses.append({
                'id': business.info['id'],
                'account': business.info['account_id'],
                'name': business.info['name']
            })

        cls.upsert(businesses)


class Client(BaseModel):
    id = IntegerField(primary_key=True)
    account = ForeignKeyField(Account)
    fname = CharField(default='')
    lname = CharField(default='')
    organization = CharField(default='')
    email = CharField(default='')

    @classmethod
    def get_the_one(cls, term):
        return cls.get(
            cls.organization == term
        )

    @classmethod
    def pull(cls, api):
        clients = []

        for business in api.businesses():
            account = business.account()
            for page in account.client_pages():
                for client in page:
                    clients.append({
                        'id': client['id'],
                        'account': account.info['id'],
                        'fname': client['fname'],
                        'lname': client['lname'],
                        'organization': client['organization'],
                        'email': client['email'],
                    })

        cls.upsert(clients)


class Project(BaseModel):
    id = IntegerField(primary_key=True)
    business = ForeignKeyField(Business)
    client_id = ForeignKeyField(Client)
    title = CharField(default='')

    @classmethod
    def pull(cls, api):
        projects = []

        for business in api.businesses():
            for page in business.project_pages():
                for project in page:
                    projects.append({
                        'id': project['id'],
                        'business': business.info['id'],
                        'client_id': project['client_id'],
                        'title': project['title'],
                    })

        cls.upsert(projects)


class Task(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField(default='')
    description = CharField(default='')

    @classmethod
    def pull(cls, api):
        tasks = []

        for business in api.businesses():
            account = business.account()
            for page in account.task_pages():
                for task in page:
                    tasks.append({
                        'id': task['id'],
                        'name': task['name'],
                        'description': task['description'],
                    })

        cls.upsert(tasks)


class TimeEntry(BaseModel):
    id = IntegerField(primary_key=True)
    client = ForeignKeyField(Client)
    project = ForeignKeyField(Project, null=True)
    task = ForeignKeyField(Task, null=True)
    created_at = DateTimeField()
    started_at = DateTimeField()
    
    # Sqlite does not store dates natively, which means that 
    # date parts cannot be extracted by certain query constructs.
    # Store the day date part separately here.
    created_at_date = DateField()
    started_at_date = DateField()

    duration = IntegerField()
    billed = BooleanField()
    billable = BooleanField()

    @classmethod
    def pull(cls, api):
        entries = []

        for business in api.businesses():
            for page in business.time_entry_pages():
                for entry in page:

                    created_at = parse_date(entry['created_at'])
                    started_at = parse_date(entry['started_at'])

                    entries.append({
                        'id': entry['id'],
                        'client': entry['client_id'],
                        'project': entry['project_id'],
                        'task': entry['task_id'],
                        'created_at': created_at,
                        'created_at_date': created_at.date(),
                        'started_at': started_at,
                        'started_at_date': started_at.date(),
                        'duration': entry['duration'],
                        'billed': entry['billed'],
                        'billable': entry['billable'],
                    })

        cls.upsert(entries)


ALL_MODELS = [
    TimeEntry,
    Task,
    Project,
    Client,
    Account,
    Business,
]


def models_by_name(names):
    models = []

    for name in names:
        name = name.lower()

        for model in ALL_MODELS:
            if model.__name__.lower() == name:
                models.append(model)

    return models