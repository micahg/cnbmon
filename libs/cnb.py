"""CNB Module."""
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1

import requests

STANDARD_HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Accept': 'application/xml, text/xml, */*; q=0.01',
    'Sec-Fetch-Dest': 'document'
}
SETTER_PATH = '/xml/setter.xml'
GETTER_PATH = '/xml/getter.xml'
LOGIN_VAL = 15
STATUS_VAL = 2
STATS_VAL = 10
LOGS_VAL = 13


class CNBError(Exception):
    """Custom CNB Exception."""

    def __init__(self, message):
        """Custom CNB Exception Constructor."""
        super().__init__(message)


class CNB:
    """CNB Class for making requests to modem."""

    def __init__(self, base_url):
        """Initialize the class."""
        self.base_url = base_url
        self.session = requests.Session()
        self.getter = f'{self.base_url}{GETTER_PATH}'
        self.setter = f'{self.base_url}{SETTER_PATH}'
        self.token = None

    def init_session(self):
        """Call the base page to get a token."""
        resp = self.session.get(self.base_url, allow_redirects=False)
        if not resp.status_code == 302:
            raise CNBError('Unable to get main page.')

        self.token = self.session.cookies.get('sessionToken')

    def get_post_data(self, fun):
        return {'token': self.token, 'fun': fun}

    def authorize(self, username, password):
        """Authorize with the modem."""
        self.init_session()
        data = self.get_post_data(LOGIN_VAL)
        data['Username'] = username
        data['Password'] = password

        resp = self.session.post(self.setter, headers=STANDARD_HEADERS, data=data)
        if not resp.status_code == 200:
            raise CNBError('Authentication failed.')

        self.token = self.session.cookies.get('sessionToken')

    def get_status(self):
        data = self.get_post_data(STATUS_VAL)
        resp = self.session.post(self.getter, headers=STANDARD_HEADERS, data=data)
        if not resp.status_code == 200:
            raise CNBError('Unable to get status.')
        return resp.content

    def get_stats(self):
        data = self.get_post_data(STATS_VAL)
        resp = self.session.post(self.getter, headers=STANDARD_HEADERS, data=data)
        if not resp.status_code == 200:
            raise CNBError('Unable to get stats.')
        return resp.content

    def get_logs(self):
        data = self.get_post_data(LOGS_VAL)
        resp = self.session.post(self.getter, headers=STANDARD_HEADERS, data=data)
        if not resp.status_code == 200:
            raise CNBError('Unable to get stats.')
        return resp.content
