from itertools import islice
from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        global running_dict
        global max_word_count
        global sub_domain_dict
        global unique_list
        global max_word_url

        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        sorted_running_dict = dict(sorted(running_dict.items(), key=lambda x: x[0], reverse=False))
        sorted_running_dict = dict(sorted(sorted_running_dict.items(), key=lambda value: value[1], reverse=True))
        temp = list(islice(sorted_running_dict, 50))
        print("\nHow many unique pages did you find: ", unique_list)
        print("\n50 most common words in the entire set of pages: ", temp)
        print("\nLongest page in terms of the # of words:", max_word_url, "with", max_word_count, "words")
        print("\nSubdomains found in the ics.uci.edu domain: ", sub_domain_dict)
        
