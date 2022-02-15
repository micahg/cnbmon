"""CNB Monitor Module."""
import sys
import argparse

import requests

from libs.cnb import CNB, CNBError
from libs.network import get_hops


DEFAULT_MODEM_URL = 'http://192.168.100.1'


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--modem-ip', action='store', dest='modem',
                    help='Modem hostname (optionally with port, eg: http://localhost:8080)')
parser.add_argument('-u', '--username', action='store', dest='user',
                    help='User name')
parser.add_argument('-p', '--password', action='store', dest='password',
                    help='Password')
args = parser.parse_args()

sess = requests.Session()

if args.user is None:
    print('USERNAME REQUIRED')
    parser.print_help()
    sys.exit()
elif args.password is None:
    print('PASSWORD REQUIRED')
    parser.print_help()
    sys.exit()

# cnb = CNB(DEFAULT_MODEM_URL if args.modem is None else args.modem)
# try:
#     cnb.authorize(args.user, args.password)
#     print('Login Succeeded')
#     status = cnb.get_status()
#     print(status)
#     stats = cnb.get_stats()
#     print(stats)
#     logs = cnb.get_logs()
#     print(logs)
# except CNBError as ex:
#     print(str(ex))

(router, gateway) = get_hops(b'start.ca')
print(f'Router is {router[0]}')
print(f'Gateway is {gateway[0]}')