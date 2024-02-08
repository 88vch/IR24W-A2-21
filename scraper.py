import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
import urllib.robotparser as robot

# Global variables to keep track of stats for the report
# unique_list is a list that will keep track of all unique pages encountered throughout the crawl
#
# running_dict is a running dictionary of all of the tokenized words and their frequencies. We will count the top 50 words.
# We still need to exclude stopwords
#
# max_word_count is the count of the webpage with the highest amount of words
#
# max_word_url holds the url of the longest page in terms of the number of words
#
# sub_domain_dict is a dictionary that contains the subdomains of the ics.uci.edu domain. The keys are the subdomains of ics.uci.edu
# and the values are the amount of unique pages on each subdomain
#
# stopwords_set is a set of stopwords to be excluded from our running_dict. Still needs to be utilized
unique_list = list()
running_dict = dict()
max_word_count = 0
max_word_url = str()
sub_domain_dict = dict()
nltk.download('stopwords')
stopwords_set = stopwords.words('english')


# Modified to take in a webpage in the form of text/string
def tokenize(page_text: str):
    """
    reads a content string and returns a list of the tokens in that page
    The time complexity is O(n) where n is the number of characters in the page
    This would make it run in polynomial time to the size of the input.
    """
    index = 0
    new_word = ""
    token_list = []
    letter = page_text[index]
    while index < len(page_text):
        val = ord(letter.lower())
        if letter.isalnum() and (97 <= val <= 122 or 48 <= val <= 57):
            new_word += letter.lower()
        else:
            if new_word != "":
                token_list.append(new_word)
            new_word = ""
        letter = page_text[index]
        index += 1
    if new_word != "":
        token_list.append(new_word)
    return token_list
def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    #
    # Global declarations to access our global variables for the report. Potentially look into better ways to store data
    global running_dict
    global max_word_count
    global sub_domain_dict
    global unique_list
    global max_word_url

    # Return if resp.status is 204 (No Content) or >= 400 (Bad Request)
    if resp.status == 204 or resp.status >= 400:
        return list()

    # Ensure we are being polite by reading a webpage's robots.txt
    # rp = robot.RobotFileParser()
    # roboturl = url + "/robots.txt"
    # rp.set_url(roboturl)
    # rp.read()
    # crawlable = rp.can_fetch("*", roboturl)

    # if robots.txt doesn't allow us to crawl we will honor it
    # if not crawlable:
    # return list()
    # Downloads webpage with BeautifulSoup
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    retList = []
    # Gets links from current webpage as listed in HTML
    links = soup.find_all('a')
    for link in links:
        link = link.get('href')
        # href is most of the time the suffix of a link ex. "/index.html"
        # we check if href does not return a full link and if it does not, we append the href
        # to the current url
        if not link == None:
            # if not link.startswith('http'):
                # link = url + link
            # Defragments the url
            split_link = link.split('#')
            add_url = split_link[0]
            if is_valid(add_url):
                retList.append(add_url)
                # if we have not encountered this page before we will add it to the unique list
                if add_url not in unique_list:
                    unique_list.append(add_url)
    # Tokenize content of current webpage
    # All words stored in list, non-unique
    # Will be repeating words in list
    word_list = []
    if len(soup.get_text()) != 0:
        word_list = tokenize(soup.get_text())

    # Checks number of words on webpage
    # If number of words greater than max, update max
    if len(word_list) > max_word_count:
        max_word_count = len(word_list)
        max_word_url = url

    # Checks each word in word_list
    # Updates running_dict
    for word in word_list:
        if word not in stopwords_set:
            if word in running_dict:
                running_dict[word] += 1
            else:
                running_dict[word] = 1

    # Checks that the current url is a subdomain of ics.uci.edu
    # If it is, make an entry in the sub_domain_dict with the number of links on the sub_domain
    if url.endswith('ics.uci.edu'):
        sub_domain_dict[url] = len(retList)

    return retList


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Gets the ending of the url
        # filtered_hostname is everything to the right of the first "."
        if parsed.hostname == None or '.' not in parsed.hostname:
            return False
        else:
            filtered_hostname = parsed.hostname.split('.', 1)[1]
        if filtered_hostname not in set(["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]):
            return False
        # Gets rid of "share=" urls
        if parsed.query is not None and "share=" in parsed.query:
            return False
        # Gets rid of calendar event paths by checking path
        if "event" in parsed.path:
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise

# Temp code for testing singular scrapes locally
# if __name__ == '__main__':
# x = download_webpage('http://vision.ics.uci.edu')
# y = scraper('http://vision.ics.uci.edu', x)
# b = download_webpage('https://ics.uci.edu')
# a = extract_next_links('https://ics.uci.edu', b)
# sorted_running_dict = dict(sorted(running_dict.items(), key=lambda x: x[0], reverse=False))
# sorted_running_dict = dict(sorted(sorted_running_dict.items(), key=lambda value: value[1], reverse=True))
# temp = list(islice(sorted_running_dict, 50))
# print("\nHow many unique pages did you find: ", unique_list)
# print("\n50 most common words in the entire set of pages: ", temp)
# print("\nLongest page in terms of the # of words:", max_word_url, "with", max_word_count, "words")
# print("\nSubdomains found in the ics.uci.edu domain: ", sub_domain_dict)
