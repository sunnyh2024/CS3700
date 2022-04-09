#!/usr/bin/env python3 

import argparse
import socket
from urllib.parse import urlparse
import ssl

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('operation', type=str)
    parser.add_argument('params', type=list, nargs='+')

    args = parser.parse_args()

    op = args.operation
    params = args.params
    SIZE = 8192

    def open_sockets(url):
        o = urlparse(url)
        control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        HOST = o.hostname
        USERNAME = o.username
        PASSWORD = o.password
        PORT = 21
        if not o.port is None:
            PORT = o.port

        #Tries to connect to server
        try:
            control_socket.connect((HOST, PORT))
            welcome = ""
            while not welcome.endswith("\r\n"):
                welcome += welcome.recv(SIZE).decode()
            print(welcome)
        except:
            print("Could not connect to server.")
            control_socket.close()
            exit(1)

        control_socket = auth(control_socket)

        data_ip, data_port = pasv(control_socket)

            # data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # try:
            #     data_socket.connect((ip, DATAPORT))
            # except:
            #     print("Could not connect to data channel.")
            #     control_socket.close()
            #     data_socket.close()
            #     exit(1)

        return control_socket, data_ip, data_port, USERNAME

    def ls(params):
        if len(params) != 1:
            print('incorrect number of arguments')
            exit(1)
        control_s, data_ip, data_port, username = open_sockets(params[0])

    def mkdir(params):
        if len(params) != 1:
            print('incorrect number of arguments')
            exit(1)
        control_s, data_ip, data_port, username = open_sockets(params[0])

    def rm(params):
        if len(params) != 1:
            print('incorrect number of arguments')
            exit(1)
        control_s, data_ip, data_port, username = open_sockets(params[0])

    def rmdir(params):
        if len(params) != 1:
            print('incorrect number of arguments')
            exit(1)
        control_s, data_ip, data_port, username = open_sockets(params[0])

    def cp(params):
        if len(params) != 2:
            print('incorrect number of arguments')
            exit(1)
        o = urlparse(params[0])
        if o.scheme != 'ftps':
            s = open_sockets(params[1])
        else:
            s = open_sockets(params[0])

    def mv(params):
        if len(params) != 2:
            print('incorrect number of arguments')
            exit(1)
        o = urlparse(params[0])
        if o.scheme != 'ftps':
            s = open_sockets(params[1])
        else:
            s = open_sockets(params[0])

# -----------------------------------------------------------

    def auth(socket):
        auth_message = "AUTH TLS\r\n"
        socket.sendall(auth_message.encode())
        auth_message = ""
        while not auth_message.endswith("\r\n"):
            auth_message += auth_message.recv(SIZE).decode()
        print(auth_message)
        socket = ssl.wrap_socket(socket)
        return socket

    # def user_and_pass(username, password, control_socket):
        

    # def pbsz(control_socket):

    # def prot(control_socket):

    # def type(control_socket):

    # def mode(control_socket):

    # def stru(control_socket):

    # def list(path, control_socket):

    # def dele(path, control_socket):

    # def mkd(path, control_socket):

    # def rmd(path, control_socket):

    # def stor(path, control_socket):

    # def retr(path, control_socket):

    # def quit(control_socket):

    def receive_message(control_socket):
        message = ""
        while not message.endswith("\r\n"):
            message += message.recv(SIZE).decode()
        print(message)

    def pasv(control_socket):
        message = "PASV \r\n"
        control_socket.sendall(message.encode())
        received_string = ""
        while not received_string.endswith("\r\n"):
            received_string += received_string.recv(SIZE).decode()
        print(received_string)
        received_string.rstrip("\r\n")
        if (received_string[:3] == "227"):
            received_array = received_string.split(" ")
            received_data = received_array[len(received_array) - 1].lstrip("(").rstrip(").").split(",")
            data_ip = f"{received_data[0]}.{received_data[1]}.{received_data[2]}.{received_data[3]}"
            data_port = int(received_data[4]) * 8 + int(received_data[5])
        else:
            print("received_string")
            control_socket.close()
            exit(1)
        return data_ip, data_port

    operations = {'ls': ls, 'mkdir': mkdir, 'rm': rm, 'rmdir': rmdir, 'cp': cp, 'mv': mv}

    if op in operations:
        operations[op](params)
    else:
        print('invalid operation')
        exit(1)




