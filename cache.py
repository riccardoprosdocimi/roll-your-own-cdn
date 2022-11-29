import csv
import gzip
import heapq
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

	def increment_views(self):
		self.views += 1


class Cache:
	def __init__(self, origin_url: str = DEFAULT_ORIGIN_URL):
		self.views = {}
		self.heap = []
		self.buffer = []
		self.origin_url = origin_url

		self.build_in_memory_cache()

	def get(self, article: str) -> bytes:
		lookup_info: LookupInfo = self.views[article]
		lookup_info.increment_views()

		if lookup_info.buffer_offset == NOT_CACHED:
			# fetch from origin and cache to disk (cache miss)
			print(f"{article}: Not cached")
			article_bytes = self.fetch_from_origin(article)
			self.save_to_disk_cache(article, article_bytes)
			lookup_info.buffer_offset = ON_DISK
		elif lookup_info.buffer_offset == ON_DISK:
			# fetch from disk and see if it qualifies for promotion (disk cache hit)
			print(f"{article}: Serving from disk cache")
			pass
		else:
			# fetch from in-memory cache (in-memory cache hit)
			print(f"{article}: Serving from in-memory cache")
			return self.buffer[lookup_info.buffer_offset]

	def increment(self, article: str):
		pass

	def build_in_memory_cache(self):
		with open("pageviews.csv") as article_file:
			reader = csv.DictReader(article_file)
			for row in reader:
				article = quote(row['article'].replace(" ", "_"))
				views = int(row["views"])

				try:
					with open(f"cache/{article}", "rb") as fd:
						self.buffer.append(fd.read())

						buffer_offset = len(self.buffer) - 1
						lookup_info = LookupInfo(views, buffer_offset)
				except IOError:
					lookup_info = LookupInfo(views, NOT_CACHED)
				finally:
					self.views[article] = lookup_info
					self.heap.append(lookup_info)

		heapq.heapify(self.heap)

	def fetch_from_origin(self, article: str) -> bytes:
		with urlopen(f"{self.origin_url}/{article}") as response:
			return response.read()

	@staticmethod
	def save_to_disk_cache(article: str, article_bytes: bytes):
		compressed_article = gzip.compress(article_bytes)
		with open(f"cache/{article}", "wb") as cache_file:
			cache_file.write(compressed_article)


if __name__ == "__main__":
	cache = Cache()
	cache.get("50_Cent")
	cache.get("Shakira")
