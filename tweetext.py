import colorama
import requests
import platform
import argparse
from pathlib import Path
import asyncio
import sys
import re
import urllib3
from colorama import Fore, Back
from tqdm import tqdm
from time import sleep
from aiohttp import ClientSession
import random
from requests_futures.sessions import FuturesSession
import bs4
from concurrent.futures import as_completed

from itertools import cycle
from shutil import get_terminal_size
from threading import Thread

class Loader:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        """
        A loader-like context manager
        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()

# checks the status of a given url
async def checkStatus(url, session: ClientSession, sem: asyncio.Semaphore, proxy_server):
    async with sem:
        if proxy_server == '':
            async with session.get(url) as response:
                return url, response.status
        else:
            async with session.get(url, proxy = proxy_server) as response:
                return url, response.status
        
    
# controls our async event loop
async def asyncStarter(url_list, semaphore_size, proxy_list):
    
    status_list = []
    headers = {'user-agent':'Mozilla/5.0 (compatible; DuckDuckBot-Https/1.1; https://duckduckgo.com/duckduckbot)'}
    proxy_server = chooseRandomProxy(proxy_list)
    
    # this will wrap our event loop and feed the the various urls to their async request function.
    async with ClientSession(headers=headers) as a_session:
        
        sem = asyncio.Semaphore(semaphore_size)

        # if aiohttp throws an error it will be caught and we'll try again up to 5 times
        for x in range(0,5):
            try:
                status_list = await asyncio.gather(*(checkStatus(u, a_session, sem, proxy_server) for u in url_list))
                break
            except:
                proxy_server = chooseRandomProxy(proxy_list)
                print(f"Error. Trying a differ proxy: {proxy_server}")
                status_list = []
                
    # return a list of the results 
    if status_list != []:   
        return status_list
    else:
        print("There was an error with aiohttp proxies. Please Try again")
        exit()

def chooseRandomProxy(proxy_list):
    if proxy_list != []:
        return "http://" + proxy_list[random.randint(0, len(proxy_list)-1)]
    else:
        return ''

colorama.init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Parse arguments passed in from command line
parser = argparse.ArgumentParser()
parser.add_argument('-u', '--username', required=True, default='')
parser.add_argument('-from', '--fromdate', required=False, default='')
parser.add_argument('-to', '--todate', required=False, default='')
parser.add_argument('--batch-size', type=int, required=False, default=300, help="How many urls to examine at once.")
parser.add_argument('--semaphore-size', type=int, required=False, default=50, help="How many urls(from --batch-size) to query at once. Between 1 and 50")
parser.add_argument('--proxy-file', required=False, default='', help="A list of proxies the script will rotate through")
args = vars(parser.parse_args())

account_name = args['username']
from_date = args['fromdate']
to_date = args['todate']
batch_size = args['batch_size']
semaphore_size = args['semaphore_size']
proxy_file = args['proxy_file']

proxy_list = []
if proxy_file != '':
    with open(proxy_file, "r") as f:
        for x in f.readlines():
            proxy_list.append(x.split("\n")[0])


remove_list = ['-', '/']
from_date = from_date.translate({ord(x): None for x in remove_list})
to_date = to_date.translate({ord(x): None for x in remove_list})
account_url = f"https://twitter.com/{account_name}"
headers = {'User-Agent': 'Mozilla/5.0 (compatible; DuckDuckBot-Https/1.1; https://duckduckgo.com/duckduckbot)'}

# Check status code
account_response = requests.get(account_url, headers=headers, allow_redirects=False)
status_code = account_response.status_code

if status_code == 200:
    print(Back.GREEN + Fore.WHITE + f"Account is ACTIVE")
elif status_code == 302:
    print(Back.RED + Fore.WHITE + f"Account is SUSPENDED. This means all of "
          f"{Back.WHITE + Fore.RED + account_name + Back.RED + Fore.WHITE}'s Tweets will be "
          f"downloaded.")
elif status_code ==429:
    print(Back.RED + Fore.WHITE + f"Respose Code 429: Too Many Requests. Your traffic to Twitter is being limited and results of this script will not be accurate")
    exit()
else:
    print(Back.RED + Fore.WHITE + f"No one currently has this handle. Twayback will search for a history of this "
          f"handle's Tweets.")
sleep(1)


wayback_cdx_url = f"https://web.archive.org/cdx/search/cdx?url=twitter.com/{account_name}/status" \
                  f"&matchType=prefix&filter=statuscode:200&mimetype:text/html&from={from_date}&to={to_date}"
cdx_page_text = requests.get(wayback_cdx_url).text

if len(re.findall(r'Blocked', cdx_page_text)) != 0:
    print(f"Sorry, no deleted Tweets can be retrieved for {account_name}.\n"
          f"This is because the Wayback Machine excludes Tweets for this handle.")
    sys.exit(-1)

# Capitalization does not matter for twitter links. Url parameters after '?' do not matter either.
# create a dict of {twitter_url: wayback_id}
tweet_id_and_url_dict = {line.split()[2].lower().split('?')[0]: line.split()[1] for line in cdx_page_text.splitlines()}

number_of_elements = len(tweet_id_and_url_dict)
if number_of_elements >= 1000:
    print(f"Getting the status codes of {number_of_elements} unique archived Tweets...\nThat's a lot of Tweets! "
          f"It's gonna take some time.\nTip: You can use -from and -to to narrow your search between two dates.")
else:
    print(f"Getting the status codes of {number_of_elements} archived Tweets...\n")

# Create a dict of wayback url
wayback_url_dict = {}
for url, number in tweet_id_and_url_dict.items():
    wayback_url_dict[number] = f"https://web.archive.org/web/{number}/{url}"

futures_list = []
tweet_class = re.compile('.*TweetTextSize TweetTextSize--jumbo.*')

# Create a dir and a txt file
directory = Path(account_name)
directory.mkdir(exist_ok=True)
f = open(f"{account_name}/{account_name}_tweets.txt", 'w')
f.close()


with FuturesSession(max_workers=5) as session:
    loader = Loader("Loading tweets...", "Done!", 0.1).start()
    for number, url in tqdm(wayback_url_dict.items(), position=0, leave=True, total=len(wayback_url_dict)):
        futures_list.append(session.get(url))
loader.stop()
sleep(1)
print("Downloading tweets...")
for future in tqdm(as_completed(futures_list), position=0, leave=True, total=len(futures_list)):
    try:
        result = future.result()
        # Take the results and put them in variables
        tweet = bs4.BeautifulSoup(result.content, "lxml").find("p", {"class": tweet_class}).getText()
        tweet_link = bs4.BeautifulSoup(result.content, "lxml").find("link", {"rel": "canonical"})['href']
        # Open file and write
        with open(f"{account_name}/{account_name}_tweets.txt", 'a') as f:
            f.write(tweet_link + "\n" + tweet + "\n---\n")
    except AttributeError:
        pass
    except ConnectionError:
        print('Connection error occurred while fetching tweet text!')
    except Exception:  # não pega MemoryError, SystemExit, KeyboardInterrupt
        pass

print(f"\nA text file ({account_name}_text.txt) is saved, which lists all URLs for the deleted Tweets and "
    f"their text, has been saved.\nYou can find it inside the folder "
    f"{Back.MAGENTA + Fore.WHITE + account_name + Back.BLACK + Fore.WHITE}.")