import gzip
import socket
import threading
from urllib.parse import unquote

import psutil


def get_local_ip() -> int:
    """
    Gets the localhost IP address.

    :return: the localhost IP address
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("www.google.com", 80))
    ip, _ = s.getsockname()
    s.close()
    return ip


def compress_article(article_raw_bytes: bytes) -> bytes:
    """
    Compresses an article object.

    :param article_raw_bytes: the uncompressed article object
    :return: the compressed article object
    """

    return gzip.compress(article_raw_bytes)


def get_avg_cpu_percent() -> float:
    """
    Gets the average CPU usage.

    :return: the average CPU usage
    """

    dict_key = "avg_cpu_percent"

    def meta(retval: dict, iterations: int = 10) -> None:
        """
        Calculates the average CPU usage in percentage.

        :param retval: a dictionary containing the average CPU usage
        :param iterations: number of measurements to be performed
        """

        avg = 0

        for _ in range(iterations):
            avg += psutil.cpu_percent(interval=0.5)

        retval[dict_key] = avg / iterations

    retval = {}
    profiling_thread = threading.Thread(target=meta, args=(retval,))
    profiling_thread.start()
    profiling_thread.join()

    return retval[dict_key]


def is_url_encoded(path: str) -> bool:
    unquoted = unquote(path)
    return path != unquoted
