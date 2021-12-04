import socket
import os
import random
import string

BUFFER_SIZE = 4096

def send_massage(massage, sock):
  sock.send(bytes(massage, "utf-8"))
  sock.recv(BUFFER_SIZE)


def rec_massage(sock):
    massage = sock.recv(BUFFER_SIZE)
    sock.send(b"i got it")
    return massage


def send_a_single_file(file_path, file_name, client_id, folder_name, socket):
    f = open(file_path, "rb")
    data_to_send = os.path.join(client_id + folder_name, file_name)
    send_massage(data_to_send, socket)
    data = f.read(BUFFER_SIZE)
    if data == b'':
        socket.send(b'empty')
    while data != b'':
        socket.send(data)
        data = f.read(BUFFER_SIZE)
    f.close()
    socket.recv(BUFFER_SIZE)


def push_all_files(directory_path, client_id, socket):
    for root, dirs, files in os.walk(directory_path, topdown=False):
        for file in files:
            name_folder = (os.path.join(root, file).split(directory_path, 1)[1]).split(file, 1)[0]
            send_a_single_file(os.path.join(root, file), file, client_id, name_folder, socket)


def pull_all_folders(path, client_socket):
    data = client_socket.recv(BUFFER_SIZE)
    # As long As the server or client has not received a message that
    # other finish send to it the folder names, continue
    while data != b'done':
        # data is the name of folder
        new_client_path = path + data.decode("utf-8")
        if not os.path.exists(new_client_path):
            os.makedirs(new_client_path)
        client_socket.send(b'got it')
        data = client_socket.recv(BUFFER_SIZE)
    client_socket.send(b'got it')


def push_all_folders(directory_path, client_id, socket):
    if client_id != '':
        client_id = os.path.join(client_id, "")
    start_path = os.sep + client_id
    for root, dirs, files in os.walk(directory_path, topdown=False):
        for name in dirs:
            path = os.path.join(root, name).split(directory_path + os.sep, 1)[1]
            send_massage(start_path + path, socket)


def get_a_single_file(path, client_socket, file_path_data):
    file_path = file_path_data.decode("utf-8")
    # send a notification that the files path has been send
    client_socket.send(b'got it')
    # create file
    file_new = path + file_path
    # changed from ab to wb!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    file = open(file_new, "wb")
    # The contents of the file
    data2 = client_socket.recv(BUFFER_SIZE)
    if data2 == b'empty':
        client_socket.send(b'got it')
    else:
        while len(data2) == BUFFER_SIZE:
            file.write(data2)
            data2 = client_socket.recv(BUFFER_SIZE)
        file.write(data2)
        client_socket.send(b'2-got it')
    file.close()


def pull_all_files(path, client_socket):
    # data = address of new folder
    data2 = client_socket.recv(BUFFER_SIZE)
    while data2 != b'it is last':
        print(data2)
        get_a_single_file(path, client_socket, data2)
        data2 = client_socket.recv(BUFFER_SIZE)
    client_socket.send(b'ok')


def delete_a_single_file_or_folder(start_path, end_path):
    new_path = os.path.join(start_path, end_path)
    if (os.path.isfile(new_path)):
        os.remove(new_path)
    if (os.path.isdir(new_path)):
        for root, dirs, files in os.walk(new_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for folder in dirs:
                os.rmdir(os.path.join(root, folder))
        os.rmdir(new_path)


def create_id():
    client_id = ""
    for i in range(0, 128):
        client_id = client_id + random.SystemRandom().choice(
            string.ascii_uppercase + string.digits + string.ascii_lowercase)
    return client_id


def names(path_folder_client, file_path):
    # print("1", path_folder_client)
    # print("2", file_path)
    # print("3", file_path.replace(os.path.join(path_folder_client, ''), ''))

    array = file_path.replace(path_folder_client + os.sep, '').split(os.sep)
    len_op_path = len(array)
    file_name = array[len_op_path - 1]
    folder_name = ''
    index = 0
    while index < len_op_path - 1:
        folder_name = os.path.join(folder_name, array[index])
        index += 1
    if folder_name != '':
        folder_name = os.sep + folder_name
    return folder_name, file_name


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def send_client_id(sock, client_id):
    sock.send(bytes(client_id, "utf-8"))









