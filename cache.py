import csv
import gzip
import heapq
import os
from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import urlopen

DEFAULT_ORIGIN_URL = "http://cs5700cdnorigin.ccs.neu.edu:8080"

NOT_CACHED = -1
ON_DISK = -2


@dataclass(order=True)
class LookupInfo:
    views: int
    buffer_offset: int
    article_name: str

    def increment_views(self):
        self.views += 1


class Cache:
    def __init__(self, origin_url: str = DEFAULT_ORIGIN_URL):
        self.views = {}
        self.heap = []
        self.buffer = []
        self.origin_url = origin_url
        self.disk_used = 0
        self.max_disk_size = 19 * 1024 * 1024  # conservatively stopping at 19MB
        self.memory_used = 0
        self.max_memory_size = 19 * 1024 * 1024  # conservatively stopping at 19MB
        self.build_in_memory_cache()

    def get(self, article: str) -> bytes:
        lookup_info: LookupInfo = self.views[article]
        lookup_info.increment_views()

        if lookup_info.buffer_offset == NOT_CACHED:
            # (CACHE MISS) fetch from origin and cache to disk
            print(f"{article}: Not cached, fetching from origin")

            article_raw_bytes = self.fetch_from_origin(article)
            compressed_article = self.compress_article(article_raw_bytes)

            if self.save_to_disk_cache(article, compressed_article):
                lookup_info.buffer_offset = ON_DISK
            else:
                print("Failed to cache article to disk")

            return compressed_article
        elif lookup_info.buffer_offset == ON_DISK:
            # (DISK CACHE HIT) fetch from disk and see if it qualifies for promotion
            print(f"{article}: Serving from disk cache")

            compressed_article = self.get_from_disk_cache(article)
            self.attempt_promotion(article, compressed_article)

            return compressed_article
        else:
            # (IN-MEMORY CACHE HIT) fetch from in-memory cache
            print(f"{article}: Serving from in-memory cache")

            return self.buffer[lookup_info.buffer_offset]

    def build_in_memory_cache(self):
        with open("pageviews.csv") as article_file:
            reader = csv.DictReader(article_file)
            for row in reader:
                article = quote(row["article"].replace(" ", "_"))
                views = int(row["views"])

                try:
                    with open(f"cache/{article}", "rb") as fd:
                        compressed_article = fd.read()

                        if not self.fits_in_memory_cache(compressed_article):
                            lookup_info = LookupInfo(views, ON_DISK, article)

                            # Don't break, continue so that any potentially smaller article
                            # down the line can be cached.
                            continue

                        self.memory_used += len(compressed_article)
                        self.buffer.append(compressed_article)

                        # Remove from disk cache
                        os.remove(f"cache/{article}")

                        buffer_offset = len(self.buffer) - 1
                        lookup_info = LookupInfo(views, buffer_offset, article)
                except IOError:
                    lookup_info = LookupInfo(views, NOT_CACHED, article)
                finally:
                    self.views[article] = lookup_info
                    self.heap.append(lookup_info)

        heapq.heapify(self.heap)

    def attempt_promotion(self, article_name_to_promote, compressed_article_to_promote):
        lookup_info_to_demote: LookupInfo = heapq.nsmallest(1, self.heap)[0]
        lookup_info_to_promote: LookupInfo = self.views[article_name_to_promote]

        eligible = lookup_info_to_demote.views < lookup_info_to_promote.views

        if eligible:
            compressed_article_to_demote = self.buffer[
                lookup_info_to_demote.buffer_offset
            ]

            swap_possible_on_disk = (
                self.disk_used
                - len(compressed_article_to_promote)
                + len(compressed_article_to_demote)
            ) <= self.max_disk_size

            swap_possible_in_memory = (
                self.memory_used
                - len(compressed_article_to_demote)
                + len(compressed_article_to_promote)
            ) <= self.max_memory_size

            if swap_possible_on_disk and swap_possible_in_memory:
                self.remove_from_disk_cache(article_name_to_promote)
                self.save_to_disk_cache(
                    lookup_info_to_demote.article_name, compressed_article_to_demote
                )
                self.buffer[
                    lookup_info_to_demote.buffer_offset
                ] = compressed_article_to_promote
                lookup_info_to_demote.buffer_offset = ON_DISK
                lookup_info_to_promote.buffer_offset = (
                    lookup_info_to_demote.buffer_offset
                )
                print(
                    f"Promoted {article_name_to_promote}, demoted {lookup_info_to_demote.article_name}"
                )

    def fetch_from_origin(self, article: str) -> bytes:
        with urlopen(f"{self.origin_url}/{article}") as response:
            return response.read()

    def remove_from_disk_cache(self, article: str):
        filepath = f"cache/{article}"
        file_size = os.path.getsize(filepath)
        os.remove(filepath)
        self.disk_used -= file_size

    def fits_in_memory_cache(self, article_raw_bytes: bytes) -> bool:
        return self.memory_used + len(article_raw_bytes) <= self.max_memory_size

    def save_to_disk_cache(self, article: str, article_raw_bytes: bytes) -> bool:
        try:
            with open(f"cache/{article}", "wb") as cache_file:
                cache_file.write(article_raw_bytes)
                self.disk_used += len(article_raw_bytes)
                return True
        except IOError:
            return False

    @staticmethod
    def get_from_disk_cache(article: str) -> bytes:
        with open(f"cache/{article}", "rb") as fd:
            return fd.read()

    @staticmethod
    def compress_article(article_raw_bytes: bytes):
        return gzip.compress(article_raw_bytes)


if __name__ == "__main__":
    cache = Cache()
    print(cache.memory_used, cache.disk_used)
