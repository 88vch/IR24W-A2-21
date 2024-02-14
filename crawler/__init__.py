from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker
from itertools import islice

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory
    
    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()
        running_dict = dict(sorted(Worker.running_dict.items(), key=lambda x: x[0], reverse=False))
        running_dict = dict(sorted(running_dict.items(), key=lambda value: value[1], reverse=True))
        temp = list(islice(running_dict, 50))
        print("\nHow many unique pages did you find: ", len(set(Worker.unique_list)))
        # print("\nUnique pages: ", Worker.unique_list)
        print("\n50 most common words in the entire set of pages: ", temp)
        print("\nLongest page in terms of the # of words:", Worker.max_word_url, "with", Worker.max_word_count, "words")
        sorted_sub_domain_dict = dict(sorted(Worker.sub_domain_dict.items(), key=lambda x: x[0], reverse=False))
        print("\nSubdomains found in the ics.uci.edu domain: ", sorted_sub_domain_dict)
        print("\nnumber of urls with near similarity: ", Worker.similarityCount) # test
    
    def join(self):
        for worker in self.workers:
            worker.join()
