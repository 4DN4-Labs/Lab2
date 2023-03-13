#!/usr/bin/python3

"""
Echo Client and Server Classes

T. D. Todd
McMaster University

to create a Client: "python EchoClientServer.py -r client" 
to create a Server: "python EchoClientServer.py -r server" 

or you can import the module into another file, e.g., 
import EchoClientServer
e.g., then do EchoClientserver.Server()

"""

########################################################################

import socket
import argparse
import sys
import csv
import pandas as pd
import json
from cryptography.fernet import Fernet


########################################################################
# Echo Server class
########################################################################

class Server:
    # Set the server hostname used to define the server socket address
    # binding. Note that "0.0.0.0" or "" serves as INADDR_ANY. i.e.,
    # bind to all local network interfaces.
    HOSTNAME = "0.0.0.0"  # All interfaces.
    # HOSTNAME = "192.168.1.22" # single interface
    # HOSTNAME = "hornet"       # valid hostname (mapped to address/IF)
    # HOSTNAME = "localhost"    # local host (mapped to local address/IF)
    # HOSTNAME = "127.0.0.1"    # same as localhost

    # Server port to bind the listen socket.
    PORT = 50000

    RECV_BUFFER_SIZE = 1024  # Used for recv.
    MAX_CONNECTION_BACKLOG = 10

    # We are sending text strings and the encoding to bytes must be
    # specified.
    # MSG_ENCODING = "ascii" # ASCII text encoding.
    MSG_ENCODING = "utf-8"  # Unicode text encoding.

    # Create server socket address. It is a tuple containing
    # address/hostname and port.
    SOCKET_ADDRESS = (HOSTNAME, PORT)

    def __init__(self):
        self.read_csv()
        self.create_listen_socket()
        self.process_connections_forever()

    def read_csv(self):
        with open('course_grades_2023.csv', mode='r') as csv_file:
            readline = csv.reader(csv_file)

            for row in readline:
                print(row)

    def create_listen_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set socket layer socket options. This one allows us to
            # reuse the socket without waiting for any timeouts.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to socket address, i.e., IP address and port.
            self.socket.bind(Server.SOCKET_ADDRESS)

            # Set socket to listen state.
            self.socket.listen(Server.MAX_CONNECTION_BACKLOG)
            print("Listening on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def process_connections_forever(self):
        try:
            while True:
                # Block while waiting for accepting incoming TCP
                # connections. When one is accepted, pass the new
                # (cloned) socket info to the connection handler
                # function. Accept returns a tuple consisting of a
                # connection reference and the remote socket address.
                self.connection_handler(self.socket.accept())
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            # If something bad happens, make sure that we close the
            # socket.
            self.socket.close()
            sys.exit(1)

    def connection_handler(self, client):
        # Unpack the client socket address tuple.
        connection, address_port = client
        print("-" * 72)
        print("Connection received from {}.".format(address_port))
        # Output the socket address.
        print(client)

        columns = {
            'GL1A': 'Lab 1',
            'GL2A': 'Lab 2',
            'GL3A': 'Lab 3',
            'GL4A': 'Lab 4',
            'GMA': 'Midterm',
            'GEA': ['Exam 1', 'Exam 2', 'Exam 3', 'Exam 4']
        }

        # encryption_keys = {
        # }

        while True:
            try:
                # Receive bytes over the TCP connection. This will block
                # until "at least 1 byte or more" is available.
                recvd_bytes = connection.recv(Server.RECV_BUFFER_SIZE)

                # If recv returns with zero bytes, the other end of the
                # TCP connection has closed (The other end is probably in
                # FIN WAIT 2 and we are in CLOSE WAIT.). If so, close the
                # server end of the connection and get the next client
                # connection.
                if len(recvd_bytes) == 0:
                    print("Closing client connection ... ")
                    connection.close()
                    break

                # Decode the received bytes back into strings. Then output
                # them.
                recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
                ID_number = recvd_str[:7]
                command = recvd_str[8:]
                print("Received " + command + " command from client")

                # Check if ID matches database
                row_num = 0
                with open('course_grades_2023.csv', mode='r') as csv_file:
                    read_line = csv.reader(csv_file)
                    for row in read_line:
                        if ID_number in row:
                            print("User found")
                            if command == "GG":
                                print("Command found")
                                df = pd.read_csv('course_grades_2023.csv')
                                student_grades = {
                                    "Student Name: ": row[0],
                                    "Student ID: ": int(row[1]),
                                    "Lab 1: ": int(row[3]),
                                    "Lab 2: ": int(row[4]),
                                    "Lab 3: ": int(row[5]),
                                    "Lab 4: ": int(row[6]),
                                    "Midterm: ": int(row[7]),
                                    "Exam 1: ": int(row[8]),
                                    "Exam 2: ": int(row[9]),
                                    "Exam 3: ": int(row[10]),
                                    "Exam 4: ": int(row[11]),
                                }
                                
                                message_send = "The requested student's grades are: \n" + json.dumps(student_grades)
                            elif command == "GEA":
                                print("Command found")
                                # Reading CSV file into a DataFrame
                                df = pd.read_csv('course_grades_2023.csv')
                                
                                exam_avg = 0
                                for exam in columns[command]:
                                    exam_avg += df[exam].mean()
                                
                                all_exam_avg = exam_avg/len(columns[command])

                                message_send = "Exam Average: " + str(all_exam_avg)
                            elif command in columns:
                                print("Command found")
                                # Reading CSV file into a DataFrame
                                df = pd.read_csv('course_grades_2023.csv')

                                # Finding the average of a column
                                col_avg = df[columns[command]].mean()
                                # # Debug print
                                # print(col_avg)

                                message_send = columns[command] + " Average : " + str(col_avg)
                            else:
                                print("Command not found. Please try again.")
                         
                            # encode message
                            message_bytes = message_send.encode('utf-8')

                            encryption_key = df.loc[row_num - 1, 'Key']
                            # # Debug print
                            # print(encryption_key)
                            encryption_key_bytes = encryption_key.encode('utf-8')

                            # Encrypt the message for transmission at the server
                            fernet = Fernet(encryption_key_bytes)
                            encrypted_message_bytes = fernet.encrypt(message_bytes)
                            connection.sendall(encrypted_message_bytes)
                            print("Sent encrypted message: ", encrypted_message_bytes)
                        row_num = row_num + 1
            

            except KeyboardInterrupt:
                print()
                print("Closing client connection ... ")
                connection.close()
                break


########################################################################
# Echo Client class
########################################################################

class Client:
    # Set the server to connect to. If the server and client are running
    # on the same machine, we can use the current hostname.
    # SERVER_HOSTNAME = socket.gethostname()
    # SERVER_HOSTNAME = "192.168.1.22"
    SERVER_HOSTNAME = "localhost"

    # Try connecting to the compeng4dn4 echo server. You need to change
    # the destination port to 50007 in the connect function below.
    # SERVER_HOSTNAME = 'compeng4dn4.mooo.com'

    # RECV_BUFFER_SIZE = 5 # Used for recv.    
    # RECV_BUFFER_SIZE = 1024  # Used for recv.
    RECV_BUFFER_SIZE = 1024

    def __init__(self):
        self.get_socket()
        self.connect_to_server()
        self.get_ID_command()

    def get_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Allow us to bind to the same port right away.            
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the client socket to a particular address/port.
            # self.socket.bind((Server.HOSTNAME, 40000))

        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connect_to_server(self):
        try:
            # Connect to the server using its socket address tuple.
            self.socket.connect((Client.SERVER_HOSTNAME, Server.PORT))
            print("Connected to \"{}\" on port {}".format(Client.SERVER_HOSTNAME, Server.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def get_console_input(self, input_message):
        # In this version we keep prompting the user until a non-blank
        # line is entered, i.e., ignore blank lines.
        while True:
            # Get student ID and command
            self.input_text = input(input_message)
            # if self.input_text[8:] != "GL1A" or "GL2A" or "GL3A" or "GL4A" or "GEA" or "GMA" or "GG":
                # print("Command Error closing server connection ...")
                # # that we close the socket.
                # self.socket.close()

            if self.input_text != "":
                break

    def process_commands(self, cmd):
        pass

    def send_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.connection_send()
                self.connection_receive()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                # If we get and error or keyboard interrupt, make sure
                # that we close the socket.
                self.socket.close()
                sys.exit(1)

    def get_ID_command(self):
        # Dictionary for ID number and key
        encryption_key = {
            '1803933':  'M7E8erO15CIh902P8DQsHxKbOADTgEPGHdiY0MplTuY=',
            '1884159':  'PWMKkdXW4VJ3pXBpr9UwjefmlIxYwPzk11Aw9TQ2wZQ=',
            '1853847':  'UVpoR9emIZDrpQ6pCLYopzE2Qm8bCrVyGEzdOOo2wXw=',
            '1810192':  'bHdhydsHzwKdb0RF4wG72yGm2a2L-CNzDl7vaWOu9KA=',
            '1891352':	'iHsXoe_5Fle-PHGtgZUCs5ariPZT-LNCUYpixMC3NxI=',
            '1811313':	'IR_IQPnIM1TI8h4USnBLuUtC72cQ-u4Fwvlu3q5npA0=',
            '1804841':	'kE8FpmTv8d8sRPIswQjCMaqunLUGoRNW6OrYU9JWZ4w=',
            '1881925':	'_B__AgO34W7urog-thBu7mRKj3AY46D8L26yedUwf0I=',
            '1877711':	'dLOM7DyrEnUsW-Q7OM6LXxZsbCFhjmyhsVT3P7oADqk=',
            '1830894':	'aM4bOtearz2GpURUxYKW23t_DlljFLzbfgWS-IRMB3U=',
            '1855191':	'-IieSn1zKJ8P3XOjyAlRcD2KbeFl_BnQjHyCE7-356w=',
            '1821012':	'Lt5wWqTM1q9gNAgME4T5-5oVptAstg9llB4A_iNAYMY=',
            '1844339':	'M6glRgMP5Y8CZIs-MbyFvev5VKW-zbWyUMMt44QCzG4=',
            '1898468':	'SS0XtthxP64E-z4oB1IsdrzJwu1PUq6hgFqP_u435AA=',
            '1883633':	'0L_o75AEsOay_ggDJtOFWkgRpvFvM0snlDm9gep786I=',
            '1808742':	'9BXraBysqT7QZLBjegET0e52WklQ7BBYWXvv8xpbvr8=',
            '1863450':	'M0PgiJutAM_L9jvyfrGDWnbfJOXmhYt_skL0S88ngkU=',
            '1830190':	'v-5GfMaI2ozfmef5BNO5hI-fEGwtKjuI1XcuTDh-wsg=',
            '1835544':	'LI14DbKGBfJExlwLodr6fkV4Pv4eABWkEhzArPbPSR8=',
            '1820930':	'zoTviAO0EACFC4rFereJuc0A-99Xf_uOdq3GiqUpoeU=',
        }

        while True:
            try:
                self.get_console_input('Please enter your ID number followed by a command: ')
                ID_command = self.connection_send()
                ID = ID_command[:7]
                command = ID_command[8:]
                
                if ID not in encryption_key:
                    print("Student ID not found. Please try again.")
                    continue
                
                print('Command entered: ' + command)
                if command == 'GMA':
                    print('Getting midterm average...')
                elif command == 'GL1A':
                    print('Getting lab 1 average...')
                elif command == 'GL2A':
                    print('Getting lab 2 average...')
                elif command == 'GL3A':
                    print('Getting lab 3 average...')
                elif command == 'GL4A':
                    print('Getting lab 4 average...')
                elif command == 'GEA':
                    print('Getting exam average...')
                elif command == 'GG':
                    print('Getting grades...')
                else:
                    print(command + " is not a valid command. Please try again from one of the following commands: GG, GEA, GMA, GL1A, GL2A, GL3A, GL4A.")
                    continue

                encrypted_message_bytes = self.connection_receive()
                print("Got encrypted message: " + encrypted_message_bytes)
                # # Debug print
                # print(encrypted_message_bytes)


                key = encryption_key[ID]
                encryption_key_bytes = key.encode('utf-8')
                # Encrypt the message for transmission at the server
                fernet = Fernet(encryption_key_bytes)
                # Decrypt the message after reception at the client.
                decrypted_message_bytes = fernet.decrypt(encrypted_message_bytes)
                decrypted_message = decrypted_message_bytes.decode('utf-8')
                print("Decrypted_message = ", decrypted_message)

            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                # If we get and error or keyboard interrupt, make sure
                # that we close the socket.
                self.socket.close()
                sys.exit(1)

    def connection_send(self):
        try:
            # Send string objects over the connection. The string must
            # be encoded into bytes objects first.
            self.socket.sendall(self.input_text.encode(Server.MSG_ENCODING))
            return self.input_text
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_receive(self):
        try:
            # Receive and print out text. The received bytes objects
            # must be decoded into string objects.
            recvd_bytes = self.socket.recv(Client.RECV_BUFFER_SIZE)

            # recv will block if nothing is available. If we receive
            # zero bytes, the connection has been closed from the
            # other end. In that case, close the connection on this
            # end and exit.
            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)

            return recvd_bytes.decode(Server.MSG_ENCODING)

        except Exception as msg:
            print(msg)
            sys.exit(1)


########################################################################
# Process command line arguments if this module is run directly.
########################################################################

# When the python interpreter runs this module directly (rather than
# importing it into another file) it sets the __name__ variable to a
# value of "__main__". If this file is imported from another module,
# then __name__ will be set to that module's name.

if __name__ == '__main__':
    roles = {'client': Client, 'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles,
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################
