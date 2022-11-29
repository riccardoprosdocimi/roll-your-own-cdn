import csv
import argparse
import gzip
import os
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import HTTPError

ORIGIN_SERVER = "cs5700cdnorigin.ccs.neu.edu"
ORIGIN_PORT = "8080"


def fetch_from_origin(path: str) -> bytes:
    with urlopen("http://" + ORIGIN_SERVER + ":" + ORIGIN_PORT + "/" + path) as response:
        return response.read()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", type=str, help="the name of the origin server")
    args = parser.parse_args()
    return args


def main():
    os.mkdir("cache")
    global ORIGIN_SERVER
    args = parse_args()
    ORIGIN_SERVER = args.o
    with open('pageviews.csv') as article_file:
        reader = csv.DictReader(article_file)
        for row in reader:
            try:
                path = quote(row['article'].replace(" ", "_"))
                article = fetch_from_origin(path)
                compressed_article = gzip.compress(article)
                with open(f"cache/{path}", "wb") as cache_file:
                    cache_file.write(compressed_article)
            except HTTPError as e:
                print(e)
                print(f"Error for this article: {row['article']}")
            except IOError:
                print("disk maxed out!!!")
                break


if __name__ == "__main__":
    main()
