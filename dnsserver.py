# import socket
import socket

from dnslib.server import DNSServer, DNSLogger, DNSRecord
from dnslib.dns import RR

HTTP_SERVER = "proj4-repl1.5700.network"
HTTP_SERVER_IP = "139.144.30.25"
DNS_SERVER = "localhost"  #"proj4-dns.5700.network"
DNS_SERVER_IP = "97.107.140.73"
PORT = 25016
IP = "cs5700cdn.example.com"
UDP_MSG_SIZE = 512


class Resolver:
    def resolve(self, request, handler):
        response = request.reply()
        response.add_answer(*RR.fromZone(f"{HTTP_SERVER}. 60 A {HTTP_SERVER_IP}"))
        print(request)
        return response


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('www.google.com', 80))

    ip, port = s.getsockname()
    s.close()

    return ip


# a = q.send(DNS_SERVER, PORT, tcp=True)
# print(DNSRecord.parse(a))
#
#
#
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind((IP, PORT))
#
#
# def build_response(data):
#     d = DNSRecord.question(IP)
#
#
# while True:
#     data, addr = sock.recvfrom(UDP_MSG_SIZE)
#     response = build_response(data)
#     sock.sendto(response, addr)

def main():
    ip = _get_local_ip()
    print(ip)
    resolver = Resolver()
    logger = DNSLogger(prefix=False)
    server = DNSServer(resolver, port=PORT, address=DNS_SERVER)
    server.start()


if __name__ == "__main__":
    main()

