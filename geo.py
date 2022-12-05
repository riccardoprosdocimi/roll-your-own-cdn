from math import radians, sin, cos, atan2, sqrt
from vendor import maxminddb
from replicas import REPLICAS

DB = maxminddb.open_database('GeoLite2-City.mmdb')
RADIUS_OF_EARTH = 6373  # km
REPLICA_LOCATIONS = dict()


def calculate_replica_locations() -> None:
    for replica in REPLICAS:
        lat, lon = locate_ip(replica[1])
        REPLICA_LOCATIONS[replica[1]] = lat, lon


calculate_replica_locations()


def locate_ip(client_ip: str) -> tuple:
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


def find_best_replica(client_ip: str) -> str:
    distances = list()
    client_lat, client_lon = locate_ip(client_ip)
    for replica, location in REPLICA_LOCATIONS.items():
        distance = haversine_distance(client_lon, client_lat, location[1], location[0])
        distances.append((distance, replica))
    return min(distances)[1]
