import json
import urllib
from util import classproperty, memoize, safe_get, pretty
from exceptions import *

USER_AGENT = 'refresh2 (python) 1.0'
VERSION = 'alpha'
PAGE_SIZE = 100


class Urls:
    TOKEN = 'https://api.freshbooks.com/auth/oauth/token'
    AUTHORIZE = 'https://my.freshbooks.com/service/auth/oauth/authorize'

    TEST = 'https://api.freshbooks.com/test'
    IDENTITY = 'https://api.freshbooks.com/auth/api/v1/users/me'

    # Business endpoints
    TIME_ENTRIES = 'https://api.freshbooks.com/timetracking/business/{BUSINESS_ID}/time_entries'
    PROJECTS = 'https://api.freshbooks.com/projects/business/{BUSINESS_ID}/projects'

    # Account  endpoints
    CLIENTS = 'https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/users/clients'
    TASKS = 'https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/projects/tasks'


def normalize_wonky_response(url, response):
    # Deal with hodge-podge freshbook api response...

    if 'message' in response:
        raise ApiError(response['message'] + ': %s' % url)
    elif 'errors' in response:
        raise ApiError('%s : %s' % (response['errors'], url))

    if 'response' in response:
        result = response['response']
    else:
        result = response

    if 'result' in result:
        result = result['result']

    pagination = {}

    if 'meta' in result:
        meta = result['meta']
        pagination = meta
    elif 'per_page' in result:
        pagination = {
            'per_page': result['per_page'],
            'pages': result['pages'],
            'page': result['page']
        }

    return pagination, result


def paginated_get(api, url, key=None, page_size=PAGE_SIZE, **kwargs):
    current_page = 1

    while True:
        kwargs.update({
            'per_page': page_size,
            'page': current_page,
        })

        response = api.get(url, **kwargs)
        pagination, result = normalize_wonky_response(url, response)

        if key is not None:
            yield safe_get(result, key)
        else:
            yield result

        if not pagination or current_page == pagination['pages']:
            break

        current_page = pagination['page'] + 1


def non_paginated_get(api, url, key=None, **kwargs):
    response = api.get(url, **kwargs)
    pagination, result = normalize_wonky_response(url, response)

    if pagination:
        raise InternalError('Unexpected paginated API endpoint: %s' % url)

    if key is not None:
        return safe_get(result, key)
    else:
        return result


class AccountApi(object):

    def __init__(self, api, account_id):
        self.api = api

        self.info = {
            'id': account_id
        }

    def client_pages(self, client=None):
        kwargs = {}

        if client is not None:
            kwargs['search[user_like]'] = client
            kwargs['search[email_like]'] = client

        return paginated_get(self, Urls.CLIENTS, key='clients')

    def task_pages(self, task_id=None):
        kwargs = {}

        if task_id is not None:
            kwargs['search[taskid]'] = task_id

        return paginated_get(self, Urls.TASKS, key='tasks')

    def get(self, url, **kwargs):
        return self.api.get(
            url.format(ACCOUNT_ID=self.info['id']), **kwargs)


class BusinessApi(object):

    def __init__(self, api, info):
        self.api = api
        self.info = info

    def account(self):
        return AccountApi(self.api, self.info['account_id'])

    def time_entry_pages(self, client_id=None):
        kwargs = {}

        if client_id is not None:
            kwargs['client_id'] = client_id

        return paginated_get(self, Urls.TIME_ENTRIES, key='time_entries')

    def project_pages(self):
        return paginated_get(self, Urls.PROJECTS, key='projects')

    def get(self, url, **kwargs):
        return self.api.get(
            url.format(BUSINESS_ID=self.info['id']), **kwargs)


class Api(object):
    def __init__(self, session):
        self.session = session
        self.update_headers(self.session)

    def test(self):
        return non_paginated_get(self, Urls.TEST)

    def identity(self):
        return non_paginated_get(self, Urls.IDENTITY)

    def businesses(self):
        businesses = []

        for membership in self._business_memberships():
            info = membership['business']
            businesses.append(BusinessApi(self, info))

        return businesses

    def business(self, business_name=None, business_id=None):
        if not business_name and not business_id:
            raise ParameterError(
                'Either business_name or business_id must be specified')
        if business_name and business_id:
            raise ParameterError(
                'Can only specify one: business_name or business_id')

        if business_name:
            info = self._business_info_by_name(business_name)
        else:
            info = self._business_info_by_id(business_id)

        return BusinessApi(self, info)

    def get(self, url, **kwargs):
        return self.session.get(url, params=kwargs).json()

    @classmethod
    def update_headers(cls, session):
        session.headers.update({
            'Api-Version': VERSION,
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json',
        })

    def _business_memberships(self):
        return non_paginated_get(self, Urls.IDENTITY, key='business_memberships')

    def _business_info_by_name(self, business_name):
        found = None
        business_name = business_name.lower()

        for membership in self._business_memberships():
            business = membership['business']
            if business['name'].lower() == business_name:
                found = business
                break

        if not found:
            raise BusinessNotFound(
                'Cannot find business by name: "%s"' % business_name)

        return found

    def _business_info_by_id(self, business_id):
        found = None

        for membership in self._business_memberships():
            business = membership['business']
            if business['id'] == business_id:
                found = business
                break

        if not found:
            raise BusinessNotFound(
                'Cannot find business by id: %s' % business_id)

        return found
