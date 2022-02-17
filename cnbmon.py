"""CNB Monitor Module."""
import sys
import argparse
import datetime
import threading
import time
import logging

from libs.cnb import CNB, CNBError
from libs.network import get_hops, do_ping, log_latency

DEFAULT_TIMEOUT = 0.25
DEFAULT_MODEM_IP = '192.168.100.1'
DEFAULT_MODEM_URL = f'http://{DEFAULT_MODEM_IP}'
PROCESSING_ABORTED = False
OUTPUT_FOLDER = '.'


def collect_host_timings(signal, host):
    timeout = DEFAULT_TIMEOUT
    timeout_ms = timeout * 1000
    while not PROCESSING_ABORTED:
        ping_ms = do_ping(host, timeout)
        if ping_ms is None or ping_ms >= timeout_ms:
            signal.set()
            timeout = timeout * 2 if timeout < 2 else 2
            timeout_ms = timeout * 1000
            logging.debug(f'Ping error or timeout at {host} ({ping_ms} {timeout_ms}). Forcing collection and expanding timeout val to {timeout}')
        else:
            timeout = DEFAULT_TIMEOUT
            timeout_ms = timeout * 1000

        dt_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_latency(host=host, ping=ping_ms, output=OUTPUT_FOLDER, ts=dt_str)
        logging.debug(f'{host} = {ping_ms} ({timeout})')
        time.sleep(1)
    logging.info(f'{host} Ping thread exiting')


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
router = router[0]
gateway = gateway[0]
modem = DEFAULT_MODEM_IP
print(f'Router is {router}')
print(f'Gateway is {gateway}')
print(f'Modem is {modem}')
#
# ping_ms = do_ping(router[0])
# print(f'{ping_ms}ms to {router[0]}')
#
# ping_ms = do_ping(gateway[0])
# print(f'{ping_ms}ms to {gateway[0]}')

event = threading.Event()
# hosts = [gateway[0], router[0]]
gateway_ping_thread = threading.Thread(target=collect_host_timings, args=(event, gateway))
router_ping_thread = threading.Thread(target=collect_host_timings, args=(event, router))
modem_ping_thread = threading.Thread(target=collect_host_timings, args=(event, modem))
modem_thread = threading.Thread(target=collect_modem_stats, args=(event,))

modem_thread.start()
gateway_ping_thread.start()
router_ping_thread.start()
modem_ping_thread.start()

print('Waiting for threads')

try:
    modem_thread.join()
    gateway_ping_thread.join()
    router_ping_thread.join()
    modem_ping_thread.join()
except KeyboardInterrupt:
    PROCESSING_ABORTED = True
    event.set()
