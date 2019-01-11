import requests
from bs4 import BeautifulSoup
import time
import random
import ConfigParser
import sys

if len(sys.argv) != 2:
    print "Config file missing!"
    print "Usage: python scraper.py <CONFIG FILE>"
    sys.exit(1)

configFile = sys.argv[1]

config = ConfigParser.ConfigParser()
config.read(configFile)

USERNAME = config.get("Config", "username")
LOGIN_NAME = config.get("Config", "login_name")
LOGIN_PASSWORD = config.get("Config", "login_password")
OUTPUT_FILENAME = config.get("Config", "output_filename")
BASE_URL = config.get("Config", "base_url")

STARTING_URL =  '%ssearch.php?keywords=&terms=all&author=%s&sc=1&sf=all&sk=t&sd=d&sr=posts&st=0&ch=300&t=0&submit=Cerca' % (BASE_URL, USERNAME)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Host': 'www.forum-calcio.com',
'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Upgrade-Insecure-Requests': '1',
'DNT': '1',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'it,en-US;q=0.9,en;q=0.8'
}

session = requests.Session()

def login():
    print "LOGIN"
    loginformurl = '%s/ucp.php?mode=login' % BASE_URL
    r = requests.get(loginformurl)
    soup = BeautifulSoup(r.text, 'html.parser')
    inputs = soup.find_all("input")
    sid = None
    for i in inputs:
        if i.get("name") == 'sid':
            sid = i.get('value')

    payload = {'username': LOGIN_NAME, 'password': LOGIN_PASSWORD, 'redirect':'index.php', 'sid':sid, 'login':'Login', 'autologin': 'on'}
    r = session.post("%sucp.php?mode=login" % BASE_URL, headers=headers, data=payload)


def getSession(url):
    session.headers.update(headers)
    r = session.get(url)
    return r

def normalize(url):
    url = url.replace('./', BASE_URL)
    return url

def parseSearchPage(url):
    out = {}
    links = []

    r = getSession(url)
    print r.headers

    soup = BeautifulSoup(r.text, 'html.parser')
    tds = soup.find_all("td", "gensmall")

    for td in tds:
        s = BeautifulSoup(td.prettify(), 'html.parser')
        if s.a:
            links.append(normalize(s.a.get('href')))

    nextLink = soup.find("a", string="Prossimo")
    if (nextLink):
        out['next'] = normalize(nextLink.get('href'))
    
    out['links'] = links
    return out

def parsePostPage(url):
    r = getSession(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    h = url.split('#')[1]
    aList = soup.find_all('a')
    theGoodOne = None
    for a in aList:
        if 'name' in a.attrs:
            if a.attrs['name'] == h:
                theGoodOne = a
    
    theTable = theGoodOne.parent.parent.parent
    postBody = theTable.find('div', 'postbody')

    quoteTitle = postBody.find('div', 'quotetitle')
    quoteBody = postBody.find('div', 'quotecontent')
    if quoteTitle:
        quoteTitle.decompose()
    if quoteBody:
        quoteBody.decompose()
    return postBody.get_text()


with open(OUTPUT_FILENAME, "w") as fp: 
    login()
    i = 1
    print "pagina %s" % i
    print STARTING_URL
    out  = parseSearchPage(STARTING_URL)
    i = i + 1
    for l in out['links']:
        post = parsePostPage(l)
        print post
        print "*"*80
        fp.write(post.encode('utf8'))
        fp.write('\n')
    while 'next' in out:
        print "pagina %s" % i
        print "PARSING %s" % out['next']
        out  = parseSearchPage(out['next'])
        i = i + 1
        for l in out['links']:
            post = parsePostPage(l)
            print post
            print "*"*80
            fp.write(post.encode('utf8'))
            fp.write('\n')
        time.sleep(5)