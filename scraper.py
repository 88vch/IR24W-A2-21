import re
from urllib.parse import urlparse
import sys


def tokenize(text_file_path):
    """
    reads a text file and returns a list of the tokens in that file
    The time complexity is O(n) where n is the number of characters in the file
    This would make it run in polynomial time to the size of the input.
    """
    try:
        token_list = []
        with open(text_file_path, 'r', encoding='utf-8') as file:
            new_word = ""
            letter = file.read(1)
            while letter:
                val = ord(letter.lower())
                if letter.isalnum() and (97 <= val <= 122 or 48 <= val <= 57):
                    new_word += letter.lower()
                else:
                    #if '\n', would still add last word in line
                    if new_word != "":
                        token_list.append(new_word)
                    new_word = ""
                letter = file.read(1)
            if new_word != "":
                token_list.append(new_word)
        return token_list
    except OSError:
        print("Error: Invalid file.")
        sys.exit()
    except UnicodeDecodeError:
        print("Error: Invalid file type.")
        sys.exit()
def computeWordFrequencies(token_list):
    """
    counts the number of occurrences of each token in the token list
    O(n) where n is the number of tokens in the list
    This would make it run in linear time to the size of the input.
    """
    token_dict = dict()
    for token in token_list:
        if token not in token_dict.keys():
            token_dict[token] = 1
        else:
            token_dict[token] += 1
    return token_dict

def similarCharacters():
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments.")
        sys.exit()
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    try:
        file1_dict = computeWordFrequencies(tokenize(file1))
        file2_dict = computeWordFrequencies(tokenize(file2))
    except OSError:
        print("Error: Invalid file.")
        sys.exit()
    except UnicodeDecodeError:
        print("Error: Invalid file type.")
        sys.exit()
    common_tokens = []
    common_count = 0
    for key in file1_dict.keys():
        if key in file2_dict:
            common_tokens.append(key)
            common_count += 1
    # for token in common_tokens:
    #     sys.stdout.write(f'{token}\n')
    print(f'{common_count}')

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
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
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
        print ("TypeError for ", parsed)
        raise
