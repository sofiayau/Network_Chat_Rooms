#
# py_client.py
# Chat Service
#

import select, socket, sys

RECV_BUFFER = 4096
PORT = 9009
if len(sys.argv) < 2:
    # Unable to get necessary info
    print "Please use [hostname] "
    sys.exit(1)
else:
    server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_connection.connect((sys.argv[1], PORT))

def prompt():
    print '>'
    end=' '
    # Flush on a file object pushes out all the data
    # that has been buffered to that point
    flush = True

print("Connected to server\n")
message_prefix = ''

socket_list = [sys.stdin, server_connection]

while True:
    # Get the sockets ready to be read through select
    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
    for s in read_sockets:
        if s is server_connection:
            # Incoming message from server
            message = s.recv(RECV_BUFFER)
            if not message:
                print("Server disconneced!")
                sys.exit(2)
            else:
                # Command to quit
                if message == '<$quit$>'.encode():
                    sys.stdout.write('Thanks for using chat service. Bye\n')
                    sys.exit(2)
                else:
                    sys.stdout.write(message.decode())
                    if 'Please login using your nickname' in message.decode():
                        message_prefix = 'name: ' # identifier for name
                    else:
                        message_prefix = ''
                    prompt()

        else:
            message = message_prefix + sys.stdin.readline()
            server_connection.sendall(message.encode())
