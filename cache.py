import csv
import heapq
from dataclasses import dataclass
from urllib.parse import quote

NOT_CACHED = -1
ON_DISK = -2


@dataclass(order=True)
class LookupInfo:
	views: int
	buffer_offset: int

	def increment(self):
		self.views += 1


class Cache:
	def __init__(self):
		self.views = {}
		self.heap = []
		self.buffer = []

		self.load_from_disk()

	def get(self, article: str) -> str:
		lookup_info: LookupInfo = self.views[article]
		lookup_info.increment()

		if lookup_info.buffer_offset == NOT_CACHED:
			pass
		elif lookup_info.buffer_offset == ON_DISK:
			pass
		else:
			print("L1 cache hit")
			return self.buffer[lookup_info.buffer_offset]

	def increment(self, article: str):
		pass

	def load_from_disk(self):
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


if __name__ == "__main__":
	cache = Cache()
	cache.get("50_Cent")
