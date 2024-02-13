import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
import urllib.robotparser as robot
from collections import defaultdict
import hashlib

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
checksum_dict = dict()
simhash_set = set()
robot_permissions_dict = dict()
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

    # Downloads webpage with BeautifulSoup
    try: 
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
    except:
        soup = BeautifulSoup(resp.raw_response.content, "utf-8")
    retList = []
    # Gets links from current webpage as listed in HTML
    links = soup.find_all('a')
    for link in links:
        link = link.get('href')
        # href is most of the time the suffix of a link ex. "/index.html"
        # we check if href does not return a full link and if it does not, we append the href
        # to the current url
        if not link == None:
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

    if isNearSimilarity(word_list):
        return retList #we don't use the url in the stats

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
    parsed = urlparse(url)
    if "www.ics.uci.edu" not in parsed:
        if ".ics.uci.edu" in parsed.hostname:
            subdomain = parsed.hostname.split(".")[0]
            fullsubdomain = "https://" + parsed.hostname
            if fullsubdomain not in sub_domain_dict:
                sub_domain_dict[fullsubdomain] = 1
            else:
                sub_domain_dict[fullsubdomain] = sub_domain_dict[fullsubdomain] + 1
    return retList


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        # check if url contains "pdf"
        for extension in {"pdf", ".zip", ".gz", ".css", ".ps", ".ppt", ".js", ".bib", ".ppsx", ".txt", ".r"}:
            if extension in url:
                return False
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
        if not robots_checkage(filtered_hostname, url): #checking robots.txt
            return False
        if parsed.query is not None:
            # Gets rid of "share=" urls, Gets rid of "action=" urls (ex. login, forgot password, etc..)
            if ("share=" in parsed.query) or ("action=" in parsed.query):
                return False
        # Gets rid of calendar event paths by checking path
        if "event" in parsed.path:
            return False

        # Deal with page traps for example .../page/200 we handle this by setting max page # as 5
        if "/page/" in parsed.path:
            splitparse = parsed.path.split("/")[-2:]
            if splitparse[1] == "":
                pagenum = int(splitparse[0])
            else:
                pagenum = int(splitparse[1])
            if pagenum <= 5:
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
        # if parsed is not None:
        print("TypeError for ", parsed)
        raise


def robots_checkage(domain, url):
    #function that checks robots.txt at root
    if domain in robot_permissions_dict:
        return robot_permissions_dict[domain].can_fetch('*', url)
    rp = robot.RobotFileParser()
    robots_url = f'https://{domain}/robots.txt'
    rp.set_url(robots_url)
    rp.read()
    robot_permissions_dict[domain] = rp
    return robot_permissions_dict[domain].can_fetch('*', url) #returns true if robot allowed on the page, false otherwise


def isExactSimilarity(url, page_text: str):
    #with checksum
    checksum = 0
    page_bytes = page_text.encode('utf-8')
    for byte in page_bytes:
        checksum += byte
    if checksum in checksum_dict:
        return True #there is an exact similarity
    checksum_dict[checksum] = url
    return False
    
    
def getFingerprint(tokens):
    # Simhash fingerprint generation
    token_dict = defaultdict(int)  # words with weights
    for token in tokens:
        token_dict[token] += 1
    # Hash tokens using SHA-256
    hash_values = [hashlib.sha256(token.encode('utf-8')).hexdigest() for token in token_dict]
    # Convert hash values to binary representation
    binary_hashes = [bin(int(hash_value, 16))[2:].zfill(256) for hash_value in hash_values]
    # Initialize fingerprint as a list of zeros
    fingerprint = ['0'] * 16  # Using 16 bits
    # Combine token weights into the fingerprint
    for i in range(len(binary_hashes)):
        for j in range(min(16, len(binary_hashes[i]))):  # Ensure 16-bit length
            if binary_hashes[i][j] == '1':
                fingerprint[j] = '1'

    return ''.join(fingerprint)



def isNearSimilarity(tokens):
    FINGER_THRESHOLD = 15
    fingerprint = getFingerprint(tokens)
    finger_similarity = 0
    for finger in simhash_set:
        for i in range(len(finger)):
            if finger[i] == fingerprint[i]:
                finger_similarity += 1
            if finger_similarity >= FINGER_THRESHOLD:
                return True
    simhash_set.add(fingerprint)
    return False