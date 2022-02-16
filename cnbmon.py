"""CNB Monitor Module."""
import sys
import argparse
import datetime
import threading
import time
import logging

from libs.cnb import CNB, CNBError
from libs.network import get_hops, do_ping, log_latency

DEFAULT_MODEM_URL = 'http://192.168.100.1'
PROCESSING_ABORTED = False
OUTPUT_FOLDER = '.'


def collect_host_timings(signal, hosts):
    while not PROCESSING_ABORTED:
        for host in hosts:
            ping_ms = do_ping(router[0])
            if ping_ms is None:
                signal.set()
                logging.info('Ping error or timeout. Forcing collection')
            else:
                dt_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                log_latency(host=host, ping=ping_ms, output=OUTPUT_FOLDER, ts=dt_str)
        time.sleep(0.1)
    logging.info('Ping thread exiting')


def collect_modem_stats(event):
    """
    Collect modem statistics.

    @param event a threading.Event that can be signalled to force immediate modem stats gathering.
    """
    cnb = CNB(DEFAULT_MODEM_URL if args.modem is None else args.modem)
    try:
        cnb.authorize(args.user, args.password)
        logging.info('Login Succeeded')
    except CNBError as ex:
        logging.error(str(ex))

    while not PROCESSING_ABORTED:
        signalled = event.wait(timeout=1)
        if signalled:
            event.clear()

        dt_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            down_stats = cnb.get_downstream()
            up_stats = cnb.get_upstream()
            # logging.debug(stats)
            # logging.info('GOT STATS')
            if signalled and not PROCESSING_ABORTED:
                logging.info('LEGITIMATE SIGNAL')
                status = cnb.get_status()
                # logging.info(status)
                logs = cnb.get_logs()
                # logging.debug(logs)
            logging.debug('collecting stats')
            cnb.log_stats(stat_string=down_stats, output=OUTPUT_FOLDER, ts=dt_str)
            cnb.log_stats(stat_string=up_stats, output=OUTPUT_FOLDER, ts=dt_str)
        except CNBError as ex:
            logging.error(str(ex))

    logging.info("Modem thread exiting")


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--modem-ip', action='store', dest='modem',
                    help='Modem hostname (optionally with port, eg: http://localhost:8080)')
parser.add_argument('-u', '--username', action='store', dest='user', help='User name')
parser.add_argument('-p', '--password', action='store', dest='password', help='Password')
parser.add_argument('-o', '--output', action='store', dest='output', help='Output folder')
parser.add_argument('-l', '--logfile', action='store', dest='log', help='Log file')
parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Debug logging')
args = parser.parse_args()

# sess = requests.Session()

if args.user is None:
    print('USERNAME REQUIRED')
    parser.print_help()
    sys.exit()
elif args.password is None:
    print('PASSWORD REQUIRED')
    parser.print_help()
    sys.exit()

if args.output:
    OUTPUT_FOLDER = args.output

# setup logging
logging.basicConfig(format='%(asctime)s: %(message)s',
                    datefmt="%H:%M:%S",
                    level=logging.DEBUG if args.debug else logging.INFO,
                    filename=args.log if args.log is not None else None)



(router, gateway) = get_hops(b'start.ca')
print(f'Router is {router[0]}')
print(f'Gateway is {gateway[0]}')
#
# ping_ms = do_ping(router[0])
# print(f'{ping_ms}ms to {router[0]}')
#
# ping_ms = do_ping(gateway[0])
# print(f'{ping_ms}ms to {gateway[0]}')

event = threading.Event()
hosts = [gateway[0], router[0]]
gateway_thread = threading.Thread(target=collect_host_timings, args=(event, hosts))
modem_thread = threading.Thread(target=collect_modem_stats, args=(event,))

modem_thread.start()
gateway_thread.start()

print('Waiting for modem thread')

try:
    modem_thread.join()
except KeyboardInterrupt:
    PROCESSING_ABORTED = True
    event.set()