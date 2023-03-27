import socket
import json
from threading import Thread
import select
from threading import Event
import time
import clock_lib

SERVER_ADDRESS = ("localhost", 50002)

MAX_CONNECTIONS = 10

INPUTS = list()
OUTPUTS = list()

input_conn_queue = list()
input_msg_queue = list()


def create_server_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(('localhost', 50002))
    server.listen(MAX_CONNECTIONS)

    return server


def conn_listener():
    while INPUTS:
        sock_read, sock_write, sock_expl = select.select(INPUTS, [], [])
        handle_readables(sock_read)


def handle_readables(readables, server_socket):
    for resource in readables:
        if resource is server_socket:
            connection, client_address = resource.accept()
            connection.setblocking(0)
            queue_item = list(("", connection))
            input_conn_queue.append(queue_item)
            INPUTS.append(connection)
            print(f"new connection from {client_address}")

        else:
            data_json = ""
            try:
                data_json = resource.recv(1024)
            except ConnectionResetError:
                pass

            if data_json:
                apod_dict = json.loads(data_json.decode())
                print(f"get new message {apod_dict}")
                if apod_dict["type"] == "reg":
                    queue_item = (apod_dict["from"], resource)
                    input_conn_queue.append(queue_item)
                elif apod_dict["type"] == "msg":
                    queue_item = ("msg", apod_dict["to"], apod_dict["from"],
                                  apod_dict["type"]).input_msg_queue.append(queue_item)
                elif apod_dict["type"] == "clk_synk":
                    print("Recieve time synk")
                    queue_item = (
                        "clk_synk", apod_dict["from"], "", time.time())
                    input_msg_queue.append(queue_item)
            else:
                clear_resource(resource)


def clear_resource(resource):
    if resource in OUTPUTS:
        OUTPUTS.remove(resource)
    if resource in INPUTS:
        INPUTS.remove(resource)
    resource.close()

    print('closing connection' + str(resource))


def listener():
    print("server is running, please, press ctrl+c to stop")
    try:
        while INPUTS:
            readables, writables, exceptionales = select.select(INPUTS, [], [])
            handle_readables(readables, server_socket)
    except KeyboardInterrupt:
        clear_resource(server_socket)
        print("Server stopped! Thank you for using!")


def worker():
    apod_dict = {}
    while(True):
        for (msg_type, msg_to, msg_from, msg) in input_msg_queue:
            for item in input_conn_queue:
                if item[0] == msg_to:
                    apod_dict["type"] = msg_type
                    apod_dict["to"] = msg_to
                    apod_dict["from"] = msg_from
                    apod_dict["msg"] = msg

                    data_json = json.dumps(apod_dict)
                    item[1].sendall(data_json.encode('utf-8'))

            input_conn_queue.remove(item)


server_socket = create_server_socket()
INPUTS.append(server_socket)

Thread(target=clock_lib.clock_face, args=("Сервер", )).start()
clock_lib.clock_curant = time.time()

Thread(target=listener).start()
Thread(target=worker).start()
