import gzip
import socket
from vendor import maxminddb

DB = maxminddb.open_database('GeoLite2-City.mmdb')


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("www.google.com", 80))
    ip, _ = s.getsockname()
    s.close()
    return ip


def compress_article(article_raw_bytes: bytes) -> bytes:
    return gzip.compress(article_raw_bytes)


def locate_ip(client_ip):
    latitude = DB.get(client_ip)['location']['latitude']
    longitude = DB.get(client_ip)['location']['longitude']
    return latitude, longitude
