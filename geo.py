from math import radians, sin, cos, atan2, sqrt

from replicas import REPLICAS
from vendor import maxminddb

DB = maxminddb.open_database('GeoLite2-City.mmdb')  # open the GeoIP database
RADIUS_OF_EARTH = 6373  # km
REPLICA_LOCATIONS = dict()


def locate_ip(client_ip: str) -> tuple:
    """
    Get the client's IP address' location.

    :param client_ip: the client's IP address
    :return: the client's IP address' latitude and longitude
    """

    lat = DB.get(client_ip)['location']['latitude']
    lon = DB.get(client_ip)['location']['longitude']
    return lat, lon


def calculate_replica_locations() -> None:
    """
    Calculates the http replica servers' location.
    """

    for replica_ip in REPLICAS.keys():
        lat, lon = locate_ip(replica_ip)
        REPLICA_LOCATIONS[replica_ip] = lat, lon


calculate_replica_locations()


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Finds distances based on latitude and longitude.

    :param lon1: the longitude of the first object
    :param lat1: the latitude of the first object
    :param lon2: the longitude of the second object
    :param lat2: the latitude of the second object
    :return: the distance
    """

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
    """
    Assigns the best http replica server to a client based on the GeoIP database.

    :param client_ip: the client's IP address
    :return: the best http replica server for a client
    """

    distances = list()
    client_lat, client_lon = locate_ip(client_ip)
    for replica, location in REPLICA_LOCATIONS.items():
        distance = haversine_distance(client_lon, client_lat, location[1], location[0])
        distances.append((distance, replica))
    return min(distances)[1]
