"""
Network module for CNB Monitor.

Most of this is borrowed from https://gist.github.com/pnc/502451. It has been
repurposed to automatically get the gateway and
"""
import sys
import socket
import struct
from ipaddress import ip_address, ip_network

CLASS_A_NETWORK = ip_network('10.0.0.0/8')
CLASS_B_NETWORK = ip_network('172.16.0.0/12')
CLASS_C_NETWORK = ip_network('192.168.1.0/24')


def get_hops(dest_name):
    """
    Get the hops.

    @returns a tuple of tuples. The first tuple is the router and the second is
             the gateway. The first element of each tuple is the IP address and
             the second is the hostname.
    """
    ttl = 1
    port = 33434

    router = None
    gateway = None

    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        timeout = struct.pack("ll", 5, 0)
        recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)

        recv_socket.bind(("", port))
        sys.stdout.write(" %d  " % ttl)
        send_socket.sendto(b'', (dest_name, port))

        finished = False
        tries = 3
        while not finished and tries > 0:
            try:
                _, curr_addr = recv_socket.recvfrom(512)
                curr_addr = curr_addr[0]
                finished = True

                try:
                    curr_name = socket.gethostbyaddr(curr_addr)
                except socket.error:
                    curr_name = curr_addr

                print(f'{curr_addr} {curr_name[0]}')
            except socket.error as err:
                print(f'{err}')
                tries -= 1

        # close down the sockets
        send_socket.close()
        recv_socket.close()

        addr = ip_address(curr_addr)
        if addr in CLASS_C_NETWORK:
            router = (curr_addr, curr_name[0])
        elif addr not in CLASS_A_NETWORK and addr not in CLASS_B_NETWORK:
            gateway = (curr_addr, curr_name[0])

        if addr not in CLASS_A_NETWORK and addr not in CLASS_B_NETWORK and addr not in CLASS_C_NETWORK:
            return router, gateway

        ttl += 1
