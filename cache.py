import csv
import heapq


class Cache:
	def __init__(self):
		self.views = {}
		self.heap = []
		self.buffer = []

		self.load_from_disk()

	def get(self, article: str) -> str:
		pass

	def increment(self, article: str):
		pass

	def load_from_disk(self):
		with open('pageviews.csv') as article_file:
			reader = csv.DictReader(article_file)
			for row in reader:
				article = row['article']

				try:
					with open(f"cache/{article}", "rb") as fd:
						self.buffer.append(fd.read())
						lookup_info = (row['views'], len(self.buffer) - 1)
						self.heap.append(lookup_info)
						heapq.heapify(self.heap)
				except IOError:
					lookup_info = (row['views'], -1)
				finally:
					self.views[article] = lookup_info


if __name__ == '__main__':
	cache = Cache()
	print(cache)
