import csv
import os
import socket
from argparse import Namespace, ArgumentParser
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

import utils

ORIGIN_SERVER = "cs5700cdnorigin.ccs.neu.edu"
ORIGIN_PORT = "8080"


def fetch_from_origin(path: str) -> bytes:
    """
    Fetches the articles objects from the origin server.

    :param path: the URL path to the article object
    :return: the article object
    """

    with urlopen(
            "http://" + ORIGIN_SERVER + ":" + ORIGIN_PORT + "/" + path
    ) as response:
        return response.read()


def parse_args() -> Namespace:
    """
    Parses the command line arguments.

    :return: the command line arguments
    """

    parser = ArgumentParser()
    parser.add_argument("-o", type=str, help="the name of the origin server")
    args = parser.parse_args()
    return args


def main():
    if not os.path.exists("cache"):  # if cache directory doesn't exist already
        os.mkdir("cache")  # create it
    global ORIGIN_SERVER
    args = parse_args()
    ORIGIN_SERVER = args.o
    with open("pageviews.csv") as article_file:  # cache the most viewed articles
        reader = csv.DictReader(article_file)
        for row in reader:
            try:
                path = quote(row["article"].replace(" ", "_"))  # replace spaces with underscores
                article = fetch_from_origin(path)  # fetch article from origin
                compressed_article = utils.compress_article(article)  # compress article
                with open(f"cache/{path}", "wb") as cache_file:  # save the compressed article as binary
                    cache_file.write(compressed_article)
            except HTTPError as e:  # error in fetching the article
                print(e)
                print(f"Error for this article: {row['article']}")
            except IOError:  # disk quota reached
                print(f"Caching complete: {socket.gethostname()}")
                break


if __name__ == "__main__":
    main()
