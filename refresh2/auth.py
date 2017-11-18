import os
import json
import threading
import webbrowser
from flask import Flask, request, session, redirect
from requests_oauthlib import OAuth2Session

import api


class TokenStore(object):

    def __init__(self, filename):
        self.filename = filename

    def save(self, token):
        with open(self.filename, 'w') as store:
            json.dump(token, store)

    def get(self):
        try:
            with open(self.filename, 'r') as store:
                return json.load(store)
        except IOError, ex:
            return None


class DeveloperWebserverFlow(object):
    PORT = 8675

    def __init__(self, client_id, client_secret, hostname='localhost'):
        self.server_thread = None
        self.token = None

        self.client_id = client_id
        self.client_secret = client_secret

        self.hostname = hostname

        self.app = Flask('refresh2-localhost-flow')

        self.app.secret_key = os.urandom(24)
        self.app.config['SESSION_TYPE'] = 'filesystem'

        self.app.add_url_rule('/', 'index', self._index)
        self.app.add_url_rule('/token', 'token', self._token)

    def begin(self):
        if not self.server_thread:
            self.server_thread = threading.Thread(
                target=self._server_thread_func)
            self.server_thread.start()

            webbrowser.open_new_tab(self._index_url)
            return self

    def wait_for_token(self):
        if self.server_thread:
            self.server_thread.join()
            return self.token
        else:
            return None

    def _server_thread_func(self):
        self.app.run(port=self.PORT, ssl_context='adhoc')

    def _stop_server(self):
        request.environ.get('werkzeug.server.shutdown')()

    def _index(self):
        target = OAuth2Session(self.client_id, redirect_uri=self._redirect_uri)
        authorize_url, state = target.authorization_url(api.Urls.AUTHORIZE)

        session['oauth_state'] = state
        return redirect(authorize_url)

    def _token(self):
        target = OAuth2Session(
            self.client_id,
            state=session['oauth_state'],
            redirect_uri=self._redirect_uri
        )

        api.Api.update_headers(target)

        token = target.fetch_token(
            api.Urls.TOKEN,
            client_secret=self.client_secret,
            authorization_response=request.url
        )

        self.token = token
        self._stop_server()
        return 'Success.  You may close this tab.'

    @property
    def _base_url(self):
        return 'https://{HOST}:{PORT}'.format(
            HOST=self.hostname,
            PORT=self.PORT
        )

    @property
    def _index_url(self):
        return self._base_url + '/'

    @property
    def _redirect_uri(self):
        return self._base_url + '/token'


def run_flow(flow, store):
    token = store.get()

    if not token:
        token = flow.begin().wait_for_token()
        store.save(token)

    session = OAuth2Session(
        flow.client_id,
        token=token,

        # Automatically store updated tokens
        auto_refresh_url=api.Urls.TOKEN,
        token_updater=lambda token: store.save(token)
    )

    return session
