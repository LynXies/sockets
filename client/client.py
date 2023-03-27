import select
import socket
import json
import time
from threading import Thread
import clock_lib

server_address = ('localhost', 50002)

hostname = "client1"

SOCKET_LIST = []
SEND_LIST = []

#request_time = 0
#response_time = 0


# Определяем переменную, в которой будет хранится структура json, и заполняем
apod_dict = {"type": "", "to": "", "from": "", "msg": ""}


def handle_readables(read_sockets):
    for resource in read_sockets:
        data_json = ""
        try:
            data_json = resource.recv(1024)
        except ConnectionResetError:
            pass
        if data_json:
            apod_dict = json.loads(data_json.decode())
            if apod_dict["type"] == "msg":
                print("Recieve msg from {address}: {msg}".format(
                    address=apod_dict["from"], msg=apod_dict["msg"]))
            elif apod_dict["type"] == "clk_synk":
                clock_lib.clock_curant = apod_dict["msg"]


def clear_resource(resource):
    if resource in SOCKET_LIST:
        SOCKET_LIST.remove(resource)
    resource.close()


def woker():
    while 1:
        try:
            read_sockets, write_sockets, error_sockets = select.select(
                SOCKET_LIST, [], [])
            handle_readables(read_sockets)
        except KeyboardInterrupt:
            clear_resource(s)
            print("Client stopped! Thank you for using!")
            break


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(server_address)

apod_dict["type"] = "reg"
apod_dict["from"] = hostname

data_json = json.dumps(apod_dict)
s.send(data_json.encode('utf-8'))

SOCKET_LIST.append(s)

Thread(target=clock_lib.clock_face, args=("Часы1", )).start()

Thread(target=woker).start()

while len(SOCKET_LIST) > 0:
    time.sleep(5)
    try:
        apod_dict["type"] = "clk_synk"
        apod_dict["to"] = ""
        apod_dict["from"] = hostname
        apod_dict["msg"] = ""

        data_json = json.dumps(apod_dict)

        s.send(data_json.encode('utf-8'))

    except OSError:
        clear_resource(s)
