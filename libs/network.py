"""
Network module for CNB Monitor.

Most of this is borrowed from https://gist.github.com/pnc/502451. It has been
repurposed to automatically get the gateway and router.

The ping stuff is from https://gist.github.com/pklaus/856268.
"""
import sys
import socket
import struct
import random
import select
import datetime
from ipaddress import ip_address, ip_network

CLASS_A_NETWORK = ip_network('10.0.0.0/8')
CLASS_B_NETWORK = ip_network('172.16.0.0/12')
CLASS_C_NETWORK = ip_network('192.168.1.0/24')

ICMP_ECHO_REQUEST = 8

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


def checksum(source_string):
    # I'm not too confident that this is right but testing seems to
    # suggest that it gives the same answers as in_cksum in ping.c.
    sum = 0
    count_to = (len(source_string) / 2) * 2
    count = 0
    while count < count_to:
        this_val = source_string[count + 1]*256+source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff # Necessary?
        count = count + 2
    if count_to < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def do_ping(host_ip, timeout=0.500):
    """
    Ping a host.

    @param host_ip the IP address of the host to ping
    @param timeout the timeout (float of seconds)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    packet_id = int((id(timeout) * random.random()) % 65535)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, packet_id, 1)
    data = bytearray(192 * 'Q', 'ascii')
    my_checksum = checksum(header + data)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,
                         socket.htons(my_checksum), packet_id, 1)
    packet = header + data
    start_time = datetime.datetime.now()
    sock.sendto(packet, (host_ip, 1))
    ready = select.select([sock], [], [], timeout)
    if not ready[0]:
        return None

    rec_packet, addr = sock.recvfrom(1024)
    end_time = datetime.datetime.now()
    type, code, _, p_id, sequence = struct.unpack('bbHHh', rec_packet[20:28])
    if p_id == packet_id:
        return (end_time - start_time).total_seconds() * 1000;

    print(f'GOT PACKET WITH UNEXPECTED ID {p_id}')
    return None
