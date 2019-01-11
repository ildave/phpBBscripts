import requests
from bs4 import BeautifulSoup
import random
import time
import markovify
import ConfigParser
import sys

if len(sys.argv) != 2:
    print "Config file missing!"
    print "Usage: python poster.py <CONFIG FILE>"
    sys.exit(1)

configFile = sys.argv[1]

config = ConfigParser.ConfigParser()
config.read(configFile)

LOGIN_NAME = config.get("Config", "login_name")
LOGIN_PASSWORD = config.get("Config", "login_password")
BASE_URL = config.get("Config", "base_url")
CORPUS = config.get("Config", "corpus")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Host': BASE_URL.replace('http://', '').replace('/', ''),
'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Upgrade-Insecure-Requests': '1',
'DNT': '1',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'it,en-US;q=0.9,en;q=0.8'
}

postHeaders = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'it,en-US;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Host': BASE_URL.replace('http://', '').replace('/', ''),
    'Origin': BASE_URL,
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}

session = requests.Session()
 
def login():
    print "LOGIN"
    loginformurl = '%sucp.php?mode=login' % BASE_URL
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
    print url
    session.headers.update(headers)
    r = session.get(url)
    return r

def postSession(url, params, ref):
    print "POST"
    postHeaders['Referer'] = ref
    session.headers.update(postHeaders)
    r = session.post(url, data=params, allow_redirects=False, cookies=session.cookies)
    return r

def normalize(url):
    url = url.replace('./', BASE_URL)
    return url

def getReplyPage(html):
    soup = BeautifulSoup(html, 'html.parser')
    img = soup.find('img', src='./styles/pubblicita/imageset/it/button_topic_reply.gif')
    a = img.parent
    return a.get('href')

def postReply(html, ref, message):
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    form = None
    for f in forms:
        if f.get("name") == 'postform':
            form = f
    action = form.get("action")
    s = BeautifulSoup(form.prettify(), 'html.parser')
    inputs = s.find_all("input")
    params = {}
    formValues = {}
    for i in inputs:
        formValues[i.get('name')] = i.get('value')

    params['subject'] = formValues['subject']
    params['addbbcode20'] = '100'
    params['helpbox'] = formValues['helpbox']
    params['message'] = message
    params['attach_sig'] = 'on'
    params['post'] = 'Invia'
    params['filecomment'] = ''
    params['topic_cur_post_id'] = formValues['topic_cur_post_id']
    params['lastclick'] = formValues['lastclick']
    params['creation_time'] = formValues['creation_time']
    params['form_token'] = formValues['form_token']

    time.sleep(10)

    postSession(normalize(action), params, ref)

def getTopic(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', class_='topictitle')
    urls = []
    for l in links:
        urls.append(l.get("href"))
    return random.choice(urls)

def generateMessage():
    with open(CORPUS) as f:
        text = f.read()
    model = markovify.NewlineText(text)
    msg = model.make_short_sentence(800, min_chars=200)
    return msg

login()

activePostsRequest = getSession('%ssearch.php?search_id=active_topics' % BASE_URL)
topicUrl = getTopic(activePostsRequest.text)

postRequest = getSession(normalize(topicUrl))
replyPageUrl = getReplyPage(postRequest.text)
replyPageRequest = getSession(normalize(replyPageUrl))

message = generateMessage()
postReply(replyPageRequest.text, replyPageUrl, message)

