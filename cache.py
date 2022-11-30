import csv
import heapq
import os
from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import urlopen

import utils

DEFAULT_ORIGIN_URL = "http://cs5700cdnorigin.ccs.neu.edu:8080"

NOT_CACHED = -1
ON_DISK = -2
APPEND = -3


@dataclass(order=True)
class LookupInfo:
    views: int
    buffer_offset: int

    # This is redundant, but sometimes we only have access to
    # LookupInfo and need to determine what article it is.
    article_name: str

    def increment_views(self):
        self.views += 1


class RepliCache:
    def __init__(self, origin_url: str = DEFAULT_ORIGIN_URL, test_mode: bool = False):
        self.articles = {}
        self.heap = []
        self.buffer = []
        self.origin_url = origin_url
        self.disk_used = 0
        self.max_disk_size = 19 * 1024 * 1024  # conservatively stopping at 19MB
        self.memory_used = 0
        self.max_memory_size = 19 * 1024 * 1024  # conservatively stopping at 19MB
        self.test_mode = test_mode
        self.build()

    def build(self):
        """
        We go through the CSV file as a starting point and then load
        those articles from disk. We fit as many as we can into memory
        and let the rest remain on disk. The ones that are moved to
        memory get deleted from the disk.

        This will lead to free space on disk that can be used for caching
        articles that might get fetched from origin.
        """
        with open("pageviews.csv") as article_file:
            reader = csv.DictReader(article_file)
            for row in reader:
                article = quote(row["article"].replace(" ", "_"))
                views = int(row["views"])

                if os.path.exists(f"cache/{article}"):
                    compressed_article = self.get_from_disk_cache(article)

                    lookup_info = self.add(article, compressed_article, views)
                    if lookup_info.buffer_offset == NOT_CACHED:
                        # Don't break, continue so that any potentially
                        # smaller article down the line can be cached.
                        continue

                    # Remove from disk cache if loaded into memory
                    if not self.test_mode and lookup_info.buffer_offset != ON_DISK:
                        os.remove(f"cache/{article}")
                else:
                    lookup_info = LookupInfo(views, NOT_CACHED, article)
                    self.articles[article] = lookup_info

        print("Cache built")

    def get(self, article: str) -> (bool, bytes):
        # Strip away leading slash from URLs
        if article[0] == "/":
            article = article[1:]

        if article not in self.articles:
            return False, None

        lookup_info: LookupInfo = self.articles[article]
        lookup_info.increment_views()
        print(lookup_info)

        if lookup_info.buffer_offset == NOT_CACHED:
            # (CACHE MISS) fetch from origin and cache to disk
            print(f"{article}: Not cached, fetching from origin")

            # Fetch article from origin and compress it
            article_raw_bytes = self.fetch_from_origin(article)
            compressed_article = utils.compress_article(article_raw_bytes)

            # Optimistically cache it to disk if we have the space
            if self.add(article, compressed_article, self.articles[article].views).buffer_offset == NOT_CACHED:
                self.attempt_evict_and_add(article, compressed_article)

            return True, compressed_article
        elif lookup_info.buffer_offset == ON_DISK:
            # (DISK CACHE HIT) fetch from disk and see if it qualifies for promotion
            print(f"{article}: Serving from disk cache")

            compressed_article = self.get_from_disk_cache(article)
            return True, compressed_article
        else:
            # (IN-MEMORY CACHE HIT) fetch from in-memory cache
            print(f"{article}: Serving from in-memory cache")

            return True, self.buffer[lookup_info.buffer_offset]

    def add(self, article: str, article_raw_bytes: bytes, views: int) -> LookupInfo:
        buffer_offset = self.add_to_in_memory_cache(article_raw_bytes)
        if buffer_offset == NOT_CACHED:
            buffer_offset = self.add_to_disk_cache(article, article_raw_bytes)

        lookup_info = LookupInfo(views, buffer_offset, article)
        if lookup_info.buffer_offset != NOT_CACHED:
            self.heap.append(lookup_info)
            self.articles[article] = lookup_info

        return lookup_info

    def add_to_in_memory_cache(
        self, article_raw_bytes: bytes, buffer_offset: int = APPEND
    ) -> int:
        if self.fits_in_memory_cache(article_raw_bytes):
            self.memory_used += len(article_raw_bytes)
            if buffer_offset == APPEND:
                self.buffer.append(article_raw_bytes)
                return len(self.buffer) - 1
            else:
                self.buffer[buffer_offset] = article_raw_bytes
                return buffer_offset

        return NOT_CACHED

    def remove_from_in_memory_cache(self, article: str) -> int:
        """
        Since buffer is a list, there's really nothing to "remove" here.
        We can set the element at the offset in the buffer to None in the
        hopes that the garbage collector reclaims that memory.

        We return the buffer_offset that is now empty in the hopes that it
        will be refilled with a new article. This method is only called by
        attempt_promotion which does exactly that, so we're safe. Otherwise,
        we would have holes in our buffer.

        :return: buffer_offset: offset within the in-memory buffer that the article occupied
        """
        lookup_info = self.articles[article]
        self.memory_used -= len(self.buffer[lookup_info.buffer_offset])
        self.buffer[lookup_info.buffer_offset] = None
        return lookup_info.buffer_offset

    def add_to_disk_cache(self, article: str, article_raw_bytes: bytes) -> int:
        try:
            with open(f"cache/{article}", "wb") as cache_file:
                cache_file.write(article_raw_bytes)
                self.disk_used += len(article_raw_bytes)
                return ON_DISK
        except IOError:
            return NOT_CACHED

    def remove_from_disk_cache(self, article: str):
        filepath = f"cache/{article}"
        file_size = os.path.getsize(filepath)
        os.remove(filepath)
        self.disk_used -= file_size

    def attempt_evict_and_add(
        self, article_name_to_promote: str, compressed_article_to_promote: bytes
    ) -> bool:
        """
        Promotion: When the cache is full, and we need to add a new article to it.

        In this situation, we find the article with minimum views from our cache and compare its
        views with that of the new article. If the new article has more views, we perform further
        checks to ensure the new article can fit in the cache (memory or disk, doesn't matter)
        once the old one is evicted. If that check succeeds, we evict the one in the cache and add
        the new one in its place.

        To make the lookup of the article with minimum views faster, we employ a heap. We run heapify
        lazily i.e. only before we need to grab the minimum element. At other times, we don't need the
        heap. This results in O(logn) heapify complexity, which is not too bad for the total number of
        articles we anticipate in the cache (~400). The logn runtime is justified because now we can
        look up the article with minimum views in O(1).
        """
        heapq.heapify(self.heap)
        lookup_info_to_evict: LookupInfo = heapq.heappop(self.heap)
        lookup_info_to_promote: LookupInfo = self.articles[article_name_to_promote]

        eligible = lookup_info_to_evict.views < lookup_info_to_promote.views

        if not eligible:
            # If we can't evict, add back to the heap
            self.heap.append(lookup_info_to_evict)
            return False
        else:
            compressed_article_to_evict = self.buffer[
                lookup_info_to_evict.buffer_offset
            ]

            return self.attempt_evict_and_add_in_memory(
                article_name_to_promote,
                lookup_info_to_promote,
                compressed_article_to_promote,
                lookup_info_to_evict,
                compressed_article_to_evict,
            ) or self.attempt_evict_and_add_on_disk(
                article_name_to_promote,
                lookup_info_to_promote,
                compressed_article_to_promote,
                lookup_info_to_evict,
                compressed_article_to_evict,
            )

    def attempt_evict_and_add_in_memory(
        self,
        article_name_to_promote: str,
        lookup_info_to_promote: LookupInfo,
        compressed_article_to_promote: bytes,
        lookup_info_to_evict: LookupInfo,
        compressed_article_to_evict: bytes,
    ) -> bool:
        swap_possible_in_memory = (
            self.memory_used
            - len(compressed_article_to_evict)
            + len(compressed_article_to_promote)
        ) <= self.max_memory_size

        if not swap_possible_in_memory:
            return False

        lookup_info_to_promote.buffer_offset = lookup_info_to_evict.buffer_offset
        lookup_info_to_evict.buffer_offset = NOT_CACHED

        deleted_buffer_offset = self.remove_from_in_memory_cache(
            lookup_info_to_evict.article_name
        )
        self.add_to_in_memory_cache(
            compressed_article_to_promote,
            deleted_buffer_offset,
        )

        print(
            f"Promoted {article_name_to_promote}, evicted {lookup_info_to_evict.article_name}"
        )
        return True

    def attempt_evict_and_add_on_disk(
        self,
        article_name_to_promote: str,
        lookup_info_to_promote: LookupInfo,
        compressed_article_to_promote: bytes,
        lookup_info_to_evict: LookupInfo,
        compressed_article_to_evict: bytes,
    ):
        swap_possible_on_disk = (
            self.disk_used
            - len(compressed_article_to_promote)
            + len(compressed_article_to_evict)
        ) <= self.max_disk_size

        if not swap_possible_on_disk:
            return False

        lookup_info_to_evict.buffer_offset = NOT_CACHED
        lookup_info_to_promote.buffer_offset = ON_DISK

        # This is the damn reason why we need to have a redundant
        # reference to article_name within LookupInfo.
        self.remove_from_disk_cache(lookup_info_to_evict.article_name)
        self.add_to_disk_cache(
            lookup_info_to_promote.article_name, compressed_article_to_promote
        )

        print(
            f"Promoted {article_name_to_promote}, evicted {lookup_info_to_evict.article_name}"
        )
        return True

    def fetch_from_origin(self, article: str) -> bytes:
        with urlopen(f"{self.origin_url}/{article}") as response:
            return response.read()

    def fits_in_memory_cache(self, article_raw_bytes: bytes) -> bool:
        return self.memory_used + len(article_raw_bytes) <= self.max_memory_size

    @staticmethod
    def get_from_disk_cache(article: str) -> bytes:
        with open(f"cache/{article}", "rb") as fd:
            return fd.read()


if __name__ == "__main__":
    cache = RepliCache(test_mode=True)
    print(cache.memory_used // 1024 / 1024, cache.disk_used // 1024 / 1024)

    from timeit import default_timer as timer

    start = timer()
    cache.get("Rishi_Sunak")
    end = timer()
    print(f"{(end - start) * 1000:.2f}ms")

    start = timer()
    cache.get("Prabhas")
    end = timer()
    print(f"{(end - start) * 1000:.2f}ms")

    start = timer()
    cache.get("Jeff_Bridges")
    end = timer()
    print(f"{(end - start) * 1000:.2f}ms")
