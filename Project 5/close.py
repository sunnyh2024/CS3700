#!/usr/bin/python3

import socket
from urllib.parse import urlparse
import argparse
from html.parser import HTMLParser
import ssl

# Network URLs
URL_BEG = 'https://fakebook.3700.network'
HOME = 'https://fakebook.3700.network/fakebook/'
LOGIN = 'https://fakebook.3700.network/accounts/login/?next=/fakebook/'
DOMAIN = 'fakebook.3700.network'

# LOGIN INFORMATION

# AD = dupuguntla.a 9L7NXJGQ6W9OJK0Z
# SH = huang.sun F59PMCWK3QF7ZB2G

# cookie information
SESSION_ID = None
CSRF_TOKEN = None
MIDDLEWARE_TOKEN = None

FLAGS = [] # Keeps track of flags found
PAGES_TO_CRAWL = [] # Queue-esque object to track the pages we still have to visit
CRAWLED_PAGES = set() # Keeps track of the visited pages

PORT = 443

# Subclass to help us handle getting URLs and getting flags
class FakebookHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global PAGES_TO_CRAWL
        global CRAWLED_PAGES

        if tag == "a":
            for pair in attrs:
                if (pair[0] == "href") and (pair[1].startswith('/')):
                    to_crawl = URL_BEG + pair[1]
                    if to_crawl not in CRAWLED_PAGES and to_crawl not in PAGES_TO_CRAWL:
                        PAGES_TO_CRAWL.append(to_crawl)

    def handle_data(self, data):
        global FLAGS
        if "FLAG: " in data:
            flag = data.split(": ")[1]
            if flag not in FLAGS:
                FLAGS.append(flag)

# Subclass to help us get the middleware token for POST requests
class LoginHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global MIDDLEWARE_TOKEN

        if tag == 'input':
            for i in range(len(attrs)):
                if (attrs[i][0] == "name") and (attrs[i][1] == "csrfmiddlewaretoken"):
                    MIDDLEWARE_TOKEN = attrs[i+1][1]

# Sends the given request and returns the received decoded data
def send(request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(100)
    sock = ssl.wrap_socket(sock)
    sock.connect((DOMAIN, PORT))
    sock.send(request.encode())
    msg = sock.recv(100000).decode()
    sock.close()
    return msg

# Sends a GET request and returns the response
def get(url):
    global CSRF_TOKEN
    global SESSION_ID

    parsed = urlparse(url)
    parsed_path = parsed.path
    if parsed_path == '':
        parsed_path = '/'
    if parsed.query:
        parsed_path += f'?{parsed.query}'

    cookie_string = cookie_to_string()
    request = f'GET {parsed_path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nConnection: close\r\nCookie: {cookie_string}\r\n\r\n'

    response = send(request)
    msg = parse_response(send(request))
    if 'csrftoken' in msg['cookies']:
        CSRF_TOKEN = msg['cookies']['csrftoken']
    if 'sessionid' in msg['cookies']:
        SESSION_ID = msg['cookies']['sessionid']
    return msg

# Sends a POST request and returns the response
def post(url, data):
    global CSRF_TOKEN
    global SESSION_ID

    parsed = urlparse(url)
    parsed_path = parsed.path
    if parsed_path == '':
        parsed_path = '/'
    if parsed.query:
        parsed_path += f'?{parsed.query}'

    cookie_string = cookie_to_string()

    request = f'POST {parsed.path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: close\r\nContent-Length: {str(len(data))}\r\nCookie: {cookie_string}\r\n\r\n{data}'
    msg = parse_response(send(request))
    if 'csrftoken' in msg['cookies']:
        CSRF_TOKEN = msg['cookies']['csrftoken']
    if 'sessionid' in msg['cookies']:
        SESSION_ID = msg['cookies']['sessionid']
    return msg

# Parses the response from the server into a dictionary 
def parse_response(data):
    response_dict = {}
    response_dict["headers"] = {}
    response_dict["cookies"] = []
    split_data = data.strip().split('\r\n\r\n')
    response_dict["body"] = split_data[-1] if len(data) > 1 else None
    headers = split_data[0].split("\r\n")
    status = headers[0].split(" ")[1]
    response_dict["status"] = status
    headers = headers[1:]
    for header in headers:
        pair = header.split(": ")
        if pair[0] == "Set-Cookie":
            response_dict["cookies"].append(pair[1])
        else:
            response_dict["headers"][pair[0]] = pair[1]

    cookie_dict = {}
    if len(response_dict['cookies']) > 0:
        cookie = response_dict['cookies'][0].split(';')
    else:
        cookie = []
        cookie_dict = {}
    for entry in cookie:
        if '=' in entry:
            entry_list = entry.split('=')
        else:
            continue
        cookie_dict[entry_list[0].lstrip()] = entry_list[1]
    response_dict['cookies'] = cookie_dict

    body_split = response_dict['body'].split('\r\n')
    for entry in body_split:
        pair = entry.split(': ')
        if pair[0] == 'Set-Cookie':
            cookie_split = pair[1].split('; ')
            info = cookie_split[0].split('=')
            if info[0] == 'csrftoken':
                response_dict['cookies']['csrftoken'] = info[1]
            if info[0] == 'sessionid':
                response_dict['cookies']['sessionid'] = info[1]

    return response_dict

# Turns the CSRF token and session ID into a string to use in GET/POST requests
def cookie_to_string():
    global CSRF_TOKEN
    global SESSION_ID

    ans = ''
    if CSRF_TOKEN:
        ans += f'csrftoken={CSRF_TOKEN}'
    if SESSION_ID:
        ans += f'sessionid={SESSION_ID}'
    if CSRF_TOKEN and SESSION_ID:
        ans = f'csrftoken={CSRF_TOKEN}; sessionid={SESSION_ID}'
    return ans

# Logs into the server
def login(info):
    global CSRF_TOKEN
    global MIDDLEWARE_TOKEN
    global SESSION_ID

    username = info[0]
    password = info[1]

    while True:
        login_page = get(LOGIN)
        if login_page['status'] == '200':
            break

    parser = LoginHTMLParser()
    CSRF_TOKEN = login_page['cookies']['csrftoken']
    parser.feed(login_page['body'])

    login_post = post(LOGIN, f'username={username}&password={password}&csrfmiddlewaretoken={MIDDLEWARE_TOKEN}&next=/fakebook/')
    CSRF_TOKEN = login_post['cookies']['csrftoken']
    SESSION_ID = login_post['cookies']['sessionid']

    # return homepage of Fakebook to start crawling
    homepage = get(HOME)
    return homepage

# Main crawl script
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)

    args = parser.parse_args()
    user_and_pass = (args.username, args.password)
    
    homepage = login(user_and_pass)
    htmlparser = FakebookHTMLParser()

    htmlparser.feed(homepage['body'])

    # Keep going until we are our of pages to crawl or until we reach 5 flags
    while len(PAGES_TO_CRAWL) > 0 and len(FLAGS) < 5:
        nextPage = PAGES_TO_CRAWL.pop()
        try:
            page_response = get(nextPage)
            status = page_response["status"]
            if status == "200":
                body = page_response["body"]
                htmlparser.feed(body)
                CRAWLED_PAGES.add(nextPage) 
            elif status == '302':
                new_url = page_response['headers']['Location']
                PAGES_TO_CRAWL.insert(0, new_url)
            elif status == '403' or status == '404':
                CRAWLED_PAGES.add(nextPage) 
            elif status == '500':
                PAGES_TO_CRAWL.insert(0, nextPage)
            else:
                PAGES_TO_CRAWL.insert(0, nextPage)
        except socket.timeout:
            print('ERROR: Timeout')
            break

    for flag in FLAGS:
        print(f'{flag}\r\n')
    
        
            