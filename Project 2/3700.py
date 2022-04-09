#!/usr/bin/env python

import sys
import argparse
import socket
from urllib.parse import urlparse
import ssl
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('operation', type=str)
    parser.add_argument('params', type=str, nargs='+')

    args = parser.parse_args()
    op = args.operation
    params = args.params

    def decode(sock):
        return sock.recv(8192).decode()

    def open_socket(url):
        '''Opens a socket and connects to host and port specified in 
        url and initializes it'''
        print(url)
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port if not parsed.port is None else 21
        username = parsed.username
        password = parsed.password
        path = parsed.path
        print(host, port, username, password, path)

        sock = socket.create_connection((host, port))
        print(decode(sock))
        sock = auth(sock)
        login(username, password, sock)
        initialize(sock)
        return sock, path

    def pasv(control):
        '''sends pasv command and returns ip and port returned by server'''
        message = 'PASV \r\n'
        control.sendall(message.encode())
        received = decode(control).rstrip('\r\n')
        print(received)
        if received.startswith('2'):
            args = received.split()
            data = args[-1].lstrip('(').rstrip(').').split(',')
            ip = '{}.{}.{}.{}'.format(data[0], data[1], data[2], data[3])
            port = (int(data[4]) << 8) + int(data[5])
        else:
            quit(control)
        return ip, port

    def auth(sock):
        '''switches to encryted socket'''
        auth_message = "AUTH TLS\r\n"
        sock.sendall(auth_message.encode())
        auth_message = decode(sock)
        print(auth_message)
        if auth_message.startswith(('4', '5', '6')):
            quit(sock)
        sock = ssl.wrap_socket(sock)
        return sock

    def login(username, password, control):
        '''helper for open_socket that logs in to the server'''
        username = 'anonymous' if username is None else username
        message = f'USER {username}\r\n'
        control.sendall(message.encode())
        received = decode(control)
        if received.startswith(('4', '5', '6')):
            quit(control)
        if received.startswith('3') and not password is None:
            message = f'PASS {password}\r\n'
            control.sendall(message.encode())
            received = decode(control)
        if received.startswith('2'):
            print('completed login')
            return message
        else: 
            print('error logging in')
            quit(control)

    def initialize(control):
        '''initializes the server to the correct settings'''
        responses = []
        message = 'PBSZ 0\r\n'
        control.sendall(message.encode())
        responses.append(decode(control))
        message = 'PROT P\r\n'
        control.sendall(message.encode())
        responses.append(decode(control))
        message = 'TYPE I\r\n'
        control.sendall(message.encode())
        responses.append(decode(control))
        message = 'MODE S\r\n'
        control.sendall(message.encode())
        responses.append(decode(control))
        message = 'STRU F\r\n'
        control.sendall(message.encode())
        responses.append(decode(control))
        for received in responses:
            if not received.startswith('2'):
                quit(control)
        print('successfully initialized')

    def quit(control, data=None):
        '''closes the given socket(s) and exits the program'''
        if not data is None:
            data.close()
        message = 'QUIT\r\n'
        control.sendall(message.encode())
        received = decode(control)
        if received[0:3] == '226':
            print(received)
        else:
            print('error closing server')
        control.close()
        sys.exit('exiting program')

    '''if statements that will handle the different operations the user can input
    into the command line.'''
    if op == 'ls':
        control, path = open_socket(params[0])
        ip, port = pasv(control)
        message = f'LIST {path}\r\n'
        control.sendall(message.encode())
        print(ip, port)
        with socket.create_connection((ip, port)) as data:
            received = decode(control)
            if received.startswith(('4', '5', '6')):
                quit(control, data)
            with ssl.wrap_socket(data) as wrapped:
                received = decode(wrapped)
                print(received)
                wrapped.unwrap()
                wrapped.close()
            data.close()
        if not received.startswith('150'):
            quit(control)
        print(received)
        received = decode(control)
        quit(control)

    if op == 'mkdir':
        control, path = open_socket(params[0])
        ip, port = pasv(control)
        message = f'MKD {path}\r\n'
        control.sendall(message.encode())
        received = decode(control)
        print(received)
        if received.startswith(('4', '5', '6')):
            quit(control)

    if op == 'rm':
        control, path = open_socket(params[0])
        ip, port = pasv(control)
        message = f'DELE {path}\r\n'
        control.sendall(message.encode())
        print(ip, port)
        received = decode(control)
        print(received)
        control.close()

    if op == 'rmdir':
        control, path = open_socket(params[0])
        ip, port = pasv(control)
        message = f'RMD {path}\r\n'
        control.sendall(message.encode())
        received = decode(control)
        print(received)
        if received.startswith(('4', '5', '6')):
            quit(control)

    if op == 'cp' or op == 'mv':
        '''copying/moving from the local machine to ftp server'''
        o1 = urlparse(params[0])
        o2 = urlparse(params[1])
        if not params[0].startswith('ftps'):
            if not params[1].startswith('ftps'):
                sys.exit('exiting program')
            remote, local = o2.path, o1.path
            control, path = open_socket(params[1])
            ip, port = pasv(control)
            message = f'STOR {remote}\r\n'
            control.sendall(message.encode())
            with socket.create_connection((ip, port)) as data:
                received = decode(control)
                print(received)
                with ssl.wrap_socket(data) as wrapped:
                    f = open(local, 'rb')
                    upload = f.read()
                    wrapped.sendall(upload)
                    f.close()
                    wrapped.unwrap()
                    wrapped.close()
                data.close()
            if op == 'mv':
                '''if the operation was 'mv', remove the file from the client side'''
                os.remove(local)
            quit(control)
        else:
            '''Copying/moving files from the server to local machine'''
            if params[1].startswith('ftps'):
                sys.exit('exiting program')
            remote, local = o1.path, o2.path
            control, path = open_socket(params[0])
            ip, port = pasv(control)
            message = f'RETR {remote}\r\n'
            control.sendall(message.encode())
            with socket.create_connection((ip, port)) as data:
                received = decode(control)
                print(received)
                with ssl.wrap_socket(data) as wrapped:
                    received = b''
                    buffer = b''
                    while True:
                        buffer = wrapped.recv(8192)
                        if buffer == b'':
                            break
                        received += buffer
                    f = open(local, 'wb')
                    f.write(received)
                    f.close()
                    wrapped.unwrap()
                    wrapped.close()
                data.close()
            if op == 'mv':
                '''if the operation was 'mv', we remove the file from the server side'''
                control, path = open_socket(params[0])
                ip, port = pasv(control)
                message = f'DELE {path}\r\n'
                control.sendall(message.encode())
                print(ip, port)
                received = decode(control)
                print(received)
            quit(control)