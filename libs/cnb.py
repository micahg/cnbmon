"""CNB Module."""
import http.client as http_client
import xml.etree.ElementTree as ET

# http_client.HTTPConnection.debuglevel = 1

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
DOWNSTREAM_VAL = 10
UPSTREAM_VAL = 11
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

    def get_downstream(self):
        data = self.get_post_data(DOWNSTREAM_VAL)
        resp = self.session.post(self.getter, headers=STANDARD_HEADERS, data=data)
        if not resp.status_code == 200:
            raise CNBError('Unable to get stats.')
        return resp.content

    def get_upstream(self):
        data = self.get_post_data(UPSTREAM_VAL)
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

    def log_stats(self, stat_string, output, ts):
        """
        Log Modem Stats ao a gnuplot compatible file

        @param stat_string the stats
        @param output the output folder
        @param ts the timestamp string

        <upstream>
		    <usid>2</usid>
		    <freq>25900000</freq>
		    <power>39</power>
		    <srate>5.120</srate>
		    <mod>64QAM</mod>
		    <channeltype>ATDMA</channeltype>
		    <bandwidth>6400000</bandwidth>
	    </upstream>

	    <downstream>
	        <freq>843000000</freq>
	        <pow>6.100</pow>
	        <snr>40</snr>
	        <mod>256QAM</mod>
	        <chid>32</chid>
	    </downstream>
        """
        root = ET.fromstring(stat_string)
        num = 0
        for child in root:

            print(child.tag)
            # bail if this doesn't have useful info
            if child.tag == 'us_num' or child.tag == 'ds_num':
                num = child.text
            if child.tag != 'downstream' and child.tag != 'upstream':
                continue

            up_down = 'up' if child.tag == 'upstream' else 'dn'
            freq = child.find('freq').text
            modulation = child.find('mod').text
            id = child.find('chid' if up_down == 'dn' else 'usid').text

            # skip bogus channels
            if id > num:
                continue

            power = child.find('pow' if up_down == 'dn' else 'power').text
            snr = child.find('snr' if up_down == 'dn' else 'srate').text
            bandwidth = None if up_down == 'dn' else child.find('bandwidth').text

            filename=f'{output}/{up_down}_{id}_{freq}_{modulation}.dat'
            # downstream is power and SNR
            line = f'{ts},{power},{snr}\n'
            if up_down == 'up':
                # upstream is power, srate? and bandwidth
                line = f'{ts},{power},{snr},{bandwidth}\n'

            with open(filename, 'a+') as file:
                file.write(line)
                file.close()
