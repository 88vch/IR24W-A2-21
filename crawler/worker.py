from itertools import islice
from threading import Thread, RLock, Semaphore
from collections import defaultdict
from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from urllib.parse import urlparse
import urllib.robotparser as robot
from bs4 import BeautifulSoup


class Worker(Thread):
    shared_dict = defaultdict(int)
    shared_lock = RLock()
    shared_semaphores = defaultdict(Semaphore)
    running_dict = dict()
    unique_list = list()
    max_word_count = 0
    max_word_url = ""
    sub_domain_dict = dict()
    similarityCount = 0
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
        # each worker gets its own similarityCount
        # self.similarityCount = 0
    def getDomain(self, url):
        try:
            parsed = urlparse(url)
            if parsed.hostname == None or '.' not in parsed.hostname:
                return None
            else:
                filtered_hostname = parsed.hostname.split('.', 1)[1]
                return filtered_hostname
        except:
            return None
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            currentDomain = self.getDomain(tbd_url)
            if currentDomain is not None:
                self.shared_semaphores[currentDomain].acquire()
                try:
                    with Worker.shared_lock:
                        Worker.shared_dict[currentDomain] += 1
                        if Worker.shared_dict[currentDomain] > 2:
                            time.sleep(self.config.time_delay)
                finally:
                    self.shared_semaphores[currentDomain].release()
                resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            try:
                robot_permissions_dict = self.robots_checkage_creation(resp)
                scraped_urls = scraper.scraper(tbd_url, resp, robot_permissions_dict)
            except:
                pass
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
            with Worker.shared_lock:
                Worker.shared_dict[currentDomain] -= 1
            with Worker.shared_lock:
                Worker.running_dict.update(scraper.running_dict)
                # self.running_dict = dict(sorted(self.running_dict.items(), key=lambda x: x[0], reverse=False))
                # self.running_dict = dict(sorted(self.running_dict.items(), key=lambda value: value[1], reverse=True))
                Worker.unique_list.extend(scraper.unique_list)
                if Worker.max_word_count < scraper.max_word_count:
                    Worker.max_word_count = scraper.max_word_count
                    Worker.max_word_url = scraper.max_word_url
                # print(scraper.sub_domain_dict)
                Worker.sub_domain_dict.update(scraper.sub_domain_dict)
                # if Worker.similarityCount != scraper.similarCount:
                #     Worker.similarityCount += 1
                # temp = list(islice(sorted_running_dict, 50))
                # print("\nHow many unique pages did you find: ", len(scraper.unique_list))
                # print("\n50 most common words in the entire set of pages: ", temp)
                # print("\nLongest page in terms of the # of words:", scraper.max_word_url, "with", scraper.max_word_count, "words")
                # sorted_sub_domain_dict = dict(sorted(scraper.sub_domain_dict.items(), key=lambda x: x[0], reverse=False))
                # print("\nSubdomains found in the ics.uci.edu domain: ", sorted_sub_domain_dict)
        similarityCount = scraper.similarCount
    def robots_checkage_creation(self, resp):
        #function that checks robots.txt at root
        robot_permissions_dict = dict()
        if resp.status == 204 or resp.status >= 400:
            return robot_permissions_dict
        robots_urls = []
        for domain in ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]:
            robots_urls.append((domain, f'https://{domain}/robots.txt'))
        for url in robots_urls:
            rp = robot.RobotFileParser()
            rp.set_url(url[1])
        # Downloads webpage with BeautifulSoup
            try: 
                soup = BeautifulSoup(resp.raw_response.content, "lxml")
            except:
                soup = BeautifulSoup(resp.raw_response.content, "utf-8")
            if len(soup.get_text()) != 0:
                rp.parse(soup.get_text())
                robot_permissions_dict[url[0]] = rp
        return robot_permissions_dict
        