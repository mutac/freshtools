import datetime
from peewee import *
from playhouse.kv import PickledKeyStore
from refresh2.util import memoize, classproperty, safe_get
from exceptions import *
from date import local_from_utc_datetime, week_ending_datetime, month_ending_datetime, year_ending_datetime


@memoize
def db():
    return SqliteDatabase('.freshtools.db')


def get_the_one_or_fail(model, **kwargs):
    try:
        return model.get_the_one(**kwargs)
    except model.DoesNotExist, ex:
        raise model.DoesNotExist('Could not find %s "%s"' % (model.__name__, str(ex)))


class MetaData(object):
    metadata = PickledKeyStore(database=db())

    @classmethod
    def table_exists(cls):
        return cls.metadata.model.table_exists()

    @classmethod
    def reset(cls):
        for key in cls.metadata.keys():
            del cls.metadata[key]

    @classmethod
    def update_last_pulled_time(cls, model, now=None):
        if now is None:
            now = datetime.datetime.now()

        last = safe_get(cls.metadata, 'last_pulled_datetime', {})
        last[model.__name__] = now
        cls.metadata['last_pulled_datetime'] = last

    @classmethod
    def get_last_pulled_time(cls, model):
        last_pull = safe_get(cls.metadata, 'last_pulled_datetime', {})
        return safe_get(last_pull, model.__name__, None)


class BaseModel(Model):
    display_fields = []

    @classproperty
    def table_name(cls):
        return cls._meta.db_table

    @classmethod
    def upsert(cls, data):
        with db().atomic():
            if len(data) > 0:
                return cls.insert_many(data).on_conflict('REPLACE').execute()
            else:
                return 0

    def show(self, print_func):
        for field, fmt in self.display_fields:
            print_func(fmt % getattr(self, field))

    @classmethod
    def get_the_one(cls, **kwargs):
        raise cls.DoesNotExist();

    class Meta:
        database = db()


class Account(BaseModel):
    id = CharField(unique=True, primary_key=True)

    display_fields = [
        ('id', 'Account ID: %s')
    ]

    @classmethod
    def pull(cls, api):
        accounts = []

        for business in api.businesses():
            account = business.account()
            accounts.append({
                'id': account.info['id']
            })

        cls.upsert(accounts)

    def __repr__(self):
        return str(self.id)


class Business(BaseModel):
    id = IntegerField(primary_key=True)
    account = ForeignKeyField(Account)
    name = CharField(default='')

    display_fields = [
        ('id', 'Business ID: %s'),
        ('account', 'Account: %s'),
        ('name', 'Business Name: %s')
    ]

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

    def __repr__(self):
        return self.name


class Client(BaseModel):
    id = IntegerField(primary_key=True)
    account = ForeignKeyField(Account)
    fname = CharField(default='')
    lname = CharField(default='')
    organization = CharField(default='')
    email = CharField(default='')

    display_fields = [
        ('id', 'Client ID: %s'),
        ('account', 'Account: %s'),
        ('organization', 'Organization: %s'),
        ('contact', 'Contact: %s')
    ]

    @property
    def contact(self):
        return ' '.join([self.fname, self.lname, '<%s>' % self.email])

    @classmethod
    def get_the_one(cls, **kwargs):
        if 'client' in kwargs:
            return cls.get(
                cls.organization**kwargs['client']
            )
        else:
            raise cls.DoesNotExist('Must specify search criteria')

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

    def __repr__(self):
        return self.organization


class Project(BaseModel):
    id = IntegerField(primary_key=True)
    business = ForeignKeyField(Business)
    client = ForeignKeyField(Client)
    title = CharField(default='')
    type = CharField(default='', null=True)
    rate = FloatField(default=0.0, null=True)
    fixed_price = FloatField(default=0.0, null=True)

    display_fields = [
        ('id', 'Project ID: %s'),
        ('business', 'Business: %s'),
        ('client', 'Client: %s'),
        ('title', 'Project: %s'),
        ('type', 'Type: %s'),
    ]

    @classmethod
    def pull(cls, api):
        projects = []

        for business in api.businesses():
            for page in business.project_pages():
                for project in page:
                    projects.append({
                        'id': project['id'],
                        'business': business.info['id'],
                        'client': project['client_id'],
                        'title': project['title'],
                        'type': project['project_type'],
                        'rate': project['rate'],
                        'fixed_price': project['fixed_price'],
                    })

        cls.upsert(projects)

    @property
    def hourly_rate(self):
        if self.type == 'hourly_rate' and self.rate:
            return self.rate
        else:
            return 0

    def __repr__(self):
        return self.title


class Task(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField(default='')
    description = CharField(default='')

    display_fields = [
        ('id', 'Task ID: %s'),
        ('name', 'Task: %s'),
        ('description', 'Description: %s'),
    ]

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

    def __repr__(self):
        return self.name


class TimeEntry(BaseModel):
    id = IntegerField(primary_key=True)
    client = ForeignKeyField(Client)
    project = ForeignKeyField(Project, null=True)
    task = ForeignKeyField(Task, null=True)
    created_at = DateTimeField()
    started_at = DateTimeField()

    #
    # Sqlite does not store dates natively, which means that 
    # date parts cannot be extracted by certain query constructs.
    # Store date parts separately.
    #
    created_at_date = DateField()
    started_at_date = DateField()
    created_at_week_ending_date = DateField()
    started_at_week_ending_date = DateField()
    created_at_month_ending_date = DateField()
    started_at_month_ending_date = DateField()
    created_at_year_ending_date = DateField()
    started_at_year_ending_date = DateField()

    duration = IntegerField()
    billed = BooleanField()
    billable = BooleanField()

    note = TextField(null=True)

    display_fields = [
        ('id', 'TimeEntry ID: %s'),
        ('client', 'Client: %s'),
        ('project', 'Project: %s'),
        ('task', 'Task: %s'),
        ('created_at', 'Entered at: %s'),
        ('duration', 'Duration (seconds): %s'),
    ]

    @classmethod
    def pull(cls, api):
        entries = []

        for business in api.businesses():
            for page in business.time_entry_pages():
                for entry in page:

                    created_at = local_from_utc_datetime(entry['created_at'])
                    started_at = local_from_utc_datetime(entry['started_at'])

                    created_at_date = created_at.date()
                    started_at_date = started_at.date()

                    created_at_week_ending_date = week_ending_datetime(created_at_date).date()
                    started_at_week_ending_date = week_ending_datetime(started_at_date).date()

                    created_at_month_ending_date = month_ending_datetime(created_at_date).date()
                    started_at_month_ending_date = month_ending_datetime(started_at_date).date()

                    created_at_year_ending_date = year_ending_datetime(created_at_date).date()
                    started_at_year_ending_date = year_ending_datetime(started_at_date).date()

                    entries.append({
                        'id': entry['id'],
                        'client': entry['client_id'],
                        'project': entry['project_id'],
                        'task': entry['task_id'],
                        'created_at': created_at,
                        'created_at_date': created_at_date,
                        'created_at_week_ending_date': created_at_week_ending_date,
                        'created_at_month_ending_date': created_at_month_ending_date,
                        'created_at_year_ending_date': created_at_year_ending_date,
                        'started_at': started_at,
                        'started_at_date': started_at_date,
                        'started_at_week_ending_date': started_at_week_ending_date,
                        'started_at_month_ending_date': started_at_month_ending_date,
                        'started_at_year_ending_date': started_at_year_ending_date,
                        'duration': entry['duration'],
                        'billed': entry['billed'],
                        'billable': entry['billable'],
                        'note': entry['note']
                    })

        cls.upsert(entries)


class LogDestination(BaseModel):
    destination = CharField(index=True)

    display_fields = [
        ('destination', '%s')
    ]

    @classmethod
    def get_the_one(cls, term):
        return cls.get(
            cls.destination == term
        )

class TaskLog(BaseModel):
    """
    This is not an actual freshbooks model, it denotes whether
    or not a TimeEntry has been logged in another, external system.
    Useful for auditing billable hours between freshbooks and
    another system.
    """
    time_entry = ForeignKeyField(TimeEntry)
    log_destination = ForeignKeyField(LogDestination)
    created_at = DateTimeField(default=datetime.datetime.now)
    created_at_date = DateField(default=datetime.datetime.now)


ALL_MODELS = [
    TimeEntry,
    Task,
    Project,
    Client,
    Account,
    Business,
    LogDestination,
    TaskLog,
]


def models_by_name(names):
    models = []

    for name in names:
        name = name.lower()

        for model in ALL_MODELS:
            if model.__name__.lower() == name:
                models.append(model)

    return models
