import gzip
import socket
from math import radians, sin, cos, atan2, sqrt
from vendor import maxminddb

DB = maxminddb.open_database('GeoLite2-City.mmdb')
RADIUS_OF_EARTH = 6373  # km


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


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    # Adapted from https://andrew.hedges.name/experiments/haversine/

    lon1, lat1 = radians(lon1), radians(lat1)
    lon2, lat2 = radians(lon2), radians(lat2)

    diff_lat = lat2 - lat1
    diff_lon = lon2 - lon1

    a = sin(diff_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(diff_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = RADIUS_OF_EARTH * c
    return d
