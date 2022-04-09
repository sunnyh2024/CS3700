#!/usr/bin/python3

import socket
from urllib.parse import urlparse
import sys
import argparse
from html.parser import HTMLParser
import ssl

#------------------------------------------
# network URLs
URL_BEG = 'https://fakebook.3700.network'
HOME = 'https://fakebook.3700.network/fakebook/'
LOGIN = 'https://fakebook.3700.network/accounts/login/?next=/fakebook/'
DOMAIN = 'fakebook.3700.network'
PORT = 443
#------------------------------------------
# GROUP LOGIN INFO
# AD = dupuguntla.a 9L7NXJGQ6W9OJK0Z
# SH = huang.sun F59PMCWK3QF7ZB2G
#------------------------------------------
# TOOK ABOUT 19 MINUTES TO SEARCH THROUGH 12654 PAGES
#------------------------------------------
SESSION_ID = None # stores current cookie's session ID
CSRF_TOKEN = None # stores current cookie's csrf token
MIDDLEWARE_TOKEN = None
FLAGS = []
PAGES_TO_CRAWL = []
CRAWLED_PAGES = set()

# Initial socket connection
SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
SOCK.settimeout(15)
context = ssl.create_default_context()
SOCK = context.wrap_socket(SOCK, server_hostname="fakebook.3700.network")
SOCK.connect((DOMAIN, PORT))

# Subclass to help us handle getting URLs and getting flags
class FakebookHTMLParser(HTMLParser):
    # finds URLs in the HTML body
    def handle_starttag(self, tag, attrs):
        global PAGES_TO_CRAWL
        global CRAWLED_PAGES
        if tag == "a":
            for pair in attrs:
                if (pair[0] == "href") and (pair[1].startswith('/')):
                    to_crawl = URL_BEG + pair[1]
                    if to_crawl not in CRAWLED_PAGES and to_crawl not in PAGES_TO_CRAWL:
                        PAGES_TO_CRAWL.append(to_crawl)

    # finds flags in the HTML body
    def handle_data(self, data):
        global FLAGS
        if "FLAG: " in data:
            flag = data.split(": ")[1]
            if flag not in FLAGS:
                FLAGS.append(flag)

# Subclass to help us handle getting the middleware token for POST requests
class LoginHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global MIDDLEWARE_TOKEN
        if tag == 'input':
            for i in range(len(attrs)):
                if (attrs[i][0] == "name") and (attrs[i][1] == "csrfmiddlewaretoken"):
                    MIDDLEWARE_TOKEN = attrs[i+1][1]

# Sends the given request through the global socket
def send(request):
    global SOCK 

    SOCK.send(request.encode())
    msg = SOCK.recv(100000).decode()
    return msg

# Reconnects the socket
def reconnect():
    global SOCK

    SOCK.close()
    SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SOCK.settimeout(5)
    context = ssl.create_default_context()
    SOCK = context.wrap_socket(SOCK, server_hostname="fakebook.3700.network")
    SOCK.connect((DOMAIN, PORT))

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
    request = f'GET {parsed_path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nConnection: keep-alive\r\nCookie: {cookie_string}\r\n\r\n'
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
    cookie_string = cookie_to_string()
    request = f'POST {parsed.path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nContent-Length: {str(len(data))}\r\nCookie: {cookie_string}\r\n\r\n{data}'
    msg = parse_response(send(request))
    if 'csrftoken' in msg['cookies']:
        CSRF_TOKEN = msg['cookies']['csrftoken']
    if 'sessionid' in msg['cookies']:
        SESSION_ID = msg['cookies']['sessionid']
    return msg

# Parses the data returned by send into a dictionary so it is more easily accessible
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

    if len(response_dict['cookies']) > 0:
        cookie = response_dict['cookies'][0].split(';')
    else:
        cookie = []
    cookie_dict = {}
    for entry in cookie:
        if entry.startswith('csrftoken') or entry.startswith('sessionid'):
            entry_list = entry.split('=')
            cookie_dict[entry_list[0].lstrip()] = entry_list[1]
    response_dict['cookies'] = cookie_dict

    body_split = response_dict['body'].split('\r\n')
    for entry in body_split:
        pair = entry.split(': ')
        if pair[0] == 'Set-Cookie':
            info = pair[1].split('; ')
            cookie_split = info[0].split('=')
            if cookie_split[0] == 'csrftoken':
                response_dict['cookies']['csrftoken'] = cookie_split[1]
            if cookie_split[0] == 'sessionid':
                response_dict['cookies']['sessionid'] = cookie_split[1]
    return response_dict

# Creates a string using the CSRF token and session ID for the Cookie parameter in requests
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

# Logs into fakebook using the given username and pasword and returns the parsed homepage
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
    
# Main script to crawl fakebook
if __name__ == '__main__':
    # Create parser to get username and password
    parser = argparse.ArgumentParser()

    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)

    args = parser.parse_args()
    user_and_pass = (args.username, args.password)
    
    # Initial login 
    homepage = login(user_and_pass)
    htmlparser = FakebookHTMLParser()
    htmlparser.feed(homepage['body'])

    # Keep going until we run out of pages or we get all the secret flags
    sent_count = 0
    while len(PAGES_TO_CRAWL) > 0 and len(FLAGS) < 5:
        nextPage = PAGES_TO_CRAWL.pop()
        try:
            page_response = get(nextPage)
            if sent_count == 100 or page_response['headers']['Connection'] == 'close':
                reconnect()
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
        print(sent_count)
        sent_count += 1

    for flag in FLAGS:
        print(f'{flag}\r\n')
    
            