import gzip
import socket
import threading

import psutil


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("www.google.com", 80))
    ip, _ = s.getsockname()
    s.close()
    return ip


def compress_article(article_raw_bytes: bytes) -> bytes:
    return gzip.compress(article_raw_bytes)


def get_avg_cpu_percent() -> float:
    dict_key = "avg_cpu_percent"

    def meta(retval: dict, iterations: int = 10):
        avg = 0

        for _ in range(iterations):
            avg += psutil.cpu_percent(interval=0.5)

        retval[dict_key] = avg / iterations

    retval = {}
    profiling_thread = threading.Thread(target=meta, args=(retval,))
    profiling_thread.start()
    profiling_thread.join()

    return retval[dict_key]
