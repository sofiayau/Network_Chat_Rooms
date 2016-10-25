#
# py_server.py
# Chat Service
#
import select, socket, sys, pdb

RECV_BUFFER = 4096
PORT = 9009
# The maximum amount of clients
MAX_CLIENTS = 30
QUIT_STRING = '<$quit$>'
host = sys.argv[1] if len(sys.argv) >= 2 else ''

def create_socket(address):
    # Address family to designate the type of address can be communicated with
    # IPv4, provides sequenced, reliable, connection-based byte streams
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set options, reuse of local addr and two sockets with same port number
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(address)
    s.listen(MAX_CLIENTS)
    # Listen for connections
    print("Listening for connection at ", address)
    return s

class Hall:
    # To hold the chat rooms
    def __init__(self):
        # {room_name: Room}
        self.rooms = {}
        # {clientName: roomName}
        self.room_client_map = {}

    def welcome_message(self, new_client):
        # Welcome message to new clients
        new_client.socket.sendall(b'Welcome to chat service.\nPlease login using your nickname:\n')
    # List used rooms
    def list_rooms(self, client):
        # No rooms now, create rooms
        if len(self.rooms) == 0:
            message = 'Sorry, there is no available room now. Please create your own!\n' \
                + 'Tips: Use [<join> room_name] to create a room.\n'
            client.socket.sendall(message.encode())
        else:
            # List available rooms currently
            message = 'Current rooms:\n'
            for room in self.rooms:
                message += room + ": " + str(len(self.rooms[room].clients)) + " client(s)\n"
            client.socket.sendall(message.encode())
    # Choice for users
    def handle_message(self, client, message):
        instructions = b'Instructions:\n'\
            + b'[<list>] List all rooms\n'\
            + b'[<join> room_name] Join/create/switch to a room\n' \
            + b'[<manual>] List all instructions\n' \
            + b'[<quit>] Quit\n' \
            + b'Happy Chatting!' \
            + b'\n'
        # Options in new connection
        print(client.name + " : " + message)
        if "name:" in message:
            name = message.split()[1]
            client.name = name
            print "Connection established from:"+ client.name
            client.socket.sendall(instructions)
        # Not enrolled in any room join/ switch/ create
        elif "<join>" in message:
            same_room = False
            # Error check
            if len(message.split()) >= 2:
                # Check the room name
                room_name = message.split()[1]
                # Judge whether you can switch the room
                if client.name in self.room_client_map:
                    if self.room_client_map[client.name] == room_name:
                        client.socket.sendall(b'You are already in room: ' + room_name.encode())
                        same_room = True
                    else: # Switch from old to new room
                        old_room = self.room_client_map[client.name]
                        self.rooms[old_room].remove_client(client)
                if not same_room:
                    # Create the new room
                    if not room_name in self.rooms:
                        new_room = Room(room_name)
                        self.rooms[room_name] = new_room
                    # Append the clients in the room
                    self.rooms[room_name].clients.append(client)
                    self.rooms[room_name].welcome_message(client)
                    self.room_client_map[client.name] = room_name

            else:
                client.socket.sendall(instructions)

        elif "<list>" in message:
            # List all the rooms
            self.list_rooms(client)

        elif "<manual>" in message:
            # Check instructions
            client.socket.sendall(instructions)

        elif "<quit>" in message:
            client.socket.sendall(QUIT_STRING.encode())
            self.remove_client(client)

        else:
            # Check if in a room or not first
            if client.name in self.room_client_map:
                self.rooms[self.room_client_map[client.name]].broadcast(client, message.encode())
            else:
                message ='You are the first user join the chat! \n' \
                    + 'You are currently not in any room! \n' \
                    + 'Use [<list>] List available rooms! \n' \
                    + 'Use [<join> room_name] Join a room! \n'
                client.socket.sendall(message.encode())

    def remove_client(self, client):
        # If a client going to quit the room
        if client.name in self.room_client_map:
            self.rooms[self.room_client_map[client.name]].remove_client(client)
            del self.room_client_map[client.name]
        print("Client: " + client.name + " has left\n")


class Room:
    def __init__(self, name):
        # A list of sockets
        self.clients = []
        self.name = name

    def welcome_message(self, from_client):
        # Welcome message in room
        message = from_client.name + "has joined the chat in " + self.name + '\n'
        for client in self.clients:
            client.socket.sendall(message.encode())

    def broadcast(self, from_client, message):
        # Send the message to all the clients in the same room
        message = from_client.name.encode() + b":" + message
        for client in self.clients:
            client.socket.sendall(message)

    def remove_client(self, client):
        self.clients.remove(client)
        leave_message = client.name.encode() + b"has left the room\n"
        self.broadcast(client, leave_message)

class Client:
    # Initialize
    def __init__(self, socket, name = "new"):
        socket.setblocking(0)
        self.socket = socket
        self.name = name
    # Return integer descriptor
    def fileno(self):
        return self.socket.fileno()


listen_sock = create_socket((host, PORT))

hall = Hall()
# Keep track of socket descriptors
connection_list = []
# Add server sockets to readable connections
connection_list.append(listen_sock)

while True:

    read_clients, write_clients, error_sockets = select.select(connection_list, [], [])
    for client in read_clients:
        # New connection request
        if client is listen_sock:
            # Extract first request from listning socket
            new_socket, add = client.accept()
            new_client = Client(new_socket)
            connection_list.append(new_client)
            hall.welcome_message(new_client)

        else: # New message sending
            message = client.socket.recv(RECV_BUFFER)
            # receiving data from the socket.
            if message:
                message = message.decode().lower()
                hall.handle_message(client, message)
            else:
                client.socket.close()
                # Remove broken sockets
                connection_list.remove(client)
    # close error sockets
    for sock in error_sockets:
        sock.close()
        connection_list.remove(sock)
