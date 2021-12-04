import socket
import os
import random
import string
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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


def send_directory(dest_path, path_folder_client, client_id, socket):
    str = dest_path.replace(path_folder_client, "")
    socket.send(bytes(client_id + str, "utf-8"))


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


def check_if_need_to_update(sock, directory, changes_from_server_dict, client_id):
    print(changes_from_server_dict)
    sock.send(bytes(client_id, "utf-8"))
    data = rec_massage(sock)
    flag_entered_to_dict = 0
    #flag_modify = 0
    while data != b'do nothing':

        flag_entered_to_dict = 1

        if data == b'create_directory':
            data2 = sock.recv(BUFFER_SIZE).decode("utf-8")
            print(data2)
            path = os.path.join(directory, data2)
            print(path)
            make_folder(path)
            changes_from_server_dict["create_directory"].append(path)

        elif data == b'create':
            data2 = sock.recv(BUFFER_SIZE)
            changes_from_server_dict["create"].append(directory + os.sep + data2.decode("utf-8"))
            get_a_single_file(directory + os.sep, sock, data2)
            # print(data2)

        elif data == b'rename_file' or data == b'modify_directory':
            data1 = rec_massage(sock)
            src_path = os.path.join(directory, data1.decode("utf-8"))
            data2 = rec_massage(sock)
            dest_path = os.path.join(directory, data2.decode("utf-8"))
            changes_from_server_dict[data.decode("utf-8")].append([src_path, dest_path])
            os.rename(src_path, dest_path)
            if data == b'modify_directory':
                flag_change_name_folder = 1

        elif data == b'modify':
            data_to_delete = rec_massage(sock).decode("utf-8")
            data_to_create = sock.recv(BUFFER_SIZE).decode("utf-8")
            print(data_to_create)
            if data_to_create[0] == os.sep:
                data_to_create= data_to_create.replace(os.sep, '', 1)
            print(data_to_delete)
            changes_from_server_dict["delete"].append(client_id + data_to_delete)
            changes_from_server_dict["create"].append(directory + os.sep + data_to_create)
            changes_from_server_dict["modify"].append(directory + os.sep + data_to_create)
            if data_to_delete[0] == os.sep:
                data_to_delete = data_to_delete.replace(os.sep, '', 1)
            delete_a_single_file_or_folder(directory, data_to_delete)
            get_a_single_file(directory + os.sep, sock, bytes(data_to_create, "utf-8"))
            flag_modify = 1

        elif data == b'delete':
            data2 = sock.recv(BUFFER_SIZE)
            for root, dirs, files in os.walk(directory + os.sep + data2.decode("utf-8"), topdown=False):
                for file in files:
                    changes_from_server_dict["delete"].append(client_id + root.replace(directory, '') + os.sep + file)
                for folder in dirs:
                    changes_from_server_dict["delete"].append(client_id + root.replace(directory, '') + os.sep + folder)
            changes_from_server_dict["delete"].append(client_id + os.sep + data2.decode("utf-8"))
            print(directory, data2.decode("utf-8"))
            delete_a_single_file_or_folder(directory, data2.decode("utf-8"))
            sock.send(b"got it")

        data = rec_massage(sock)

    return flag_entered_to_dict


def send_client_id(sock, client_id):
    sock.send(bytes(client_id, "utf-8"))


def send_new_folder_path(src_path, dest_path, directory, socket, client_id):
    str_src_path = src_path.replace(directory, "")
    str_dest_path = dest_path.replace(directory, "")
    path_dest_arr = str_dest_path.split(os.sep)
    path_src_arr = str_src_path.split(os.sep)
    folder_new_name = path_dest_arr[0]
    folder_old_name = path_src_arr[0]
    if folder_new_name == folder_old_name:
        for i in range(1, len(path_dest_arr)):
            if path_dest_arr[i] == path_src_arr[i]:
                folder_old_name = os.path.join(folder_old_name, path_src_arr[i])
                folder_new_name = os.path.join(folder_new_name, path_dest_arr[i])
            if path_dest_arr[i] != path_src_arr[i]:
                folder_old_name = os.path.join(folder_old_name, path_src_arr[i])
                folder_new_name = os.path.join(folder_new_name, path_dest_arr[i])
                break
    send_massage(os.path.join(client_id, folder_old_name, socket))
    send_massage(os.path.join(client_id, folder_new_name, socket))



class Watcher:

    def __init__(self, directory, times, ip, port, client_id, computer_id, handler):
        self.observer = Observer()
        self.directory = directory
        self.time_for_connect = times
        self.ip = ip
        self.port = port
        self.client_id = client_id
        self.computer_id = computer_id
        self.handler = handler
        self.changes_from_server_dict = {"delete": [], "create": [], "create_directory": [], "rename_file": [],
                                         "modify_directory": [], "modify": []}

    def run(self):
        self.observer.schedule(self.handler, self.directory, recursive=True)
        self.observer.start()

        print("\nWatcher Running in {}/\n".format(self.directory))
        try:
            while True:
                self.handler.close_socket()
                time.sleep(self.time_for_connect)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.handler.set_socket(sock)
                sock.connect((self.ip, self.port))
                sock.send(bytes(self.computer_id, "utf-8"))
                a = sock.recv(BUFFER_SIZE)
                print(a)
                flag_erease_dict = check_if_need_to_update(sock, self.directory, self.changes_from_server_dict,
                                                             self.client_id)
                dict = self.handler.get_dict()
                print("change from sever:", self.changes_from_server_dict)
                print("change from client", dict)

                for item in dict["create_directory"]:
                    if item not in self.changes_from_server_dict["create_directory"]:
                        send_massage("create_directory", sock)
                        send_massage(self.client_id, sock)
                        send_directory(item, self.directory, self.client_id, sock)

                for item in dict["create"]:
                    if item not in self.changes_from_server_dict["create"]:
                        send_massage("create", sock)
                        send_massage(self.client_id, sock)
                        folder_name, file_name = names(self.directory, item)
                        send_a_single_file(item, file_name, os.sep + self.client_id, folder_name, sock)

                for item in dict["rename_file"]:
                    if item not in self.changes_from_server_dict["rename_file"]:
                        send_massage("rename_file", sock)
                        send_massage(self.client_id, sock)
                        folder_name1, file_name1 = names(self.directory, item[0])
                        # delete os.sep-
                        send_massage(self.client_id + folder_name1 + os.sep + file_name1, sock)
                        folder_name2, file_name2 = names(self.directory, item[1])
                        send_massage(self.client_id + folder_name2 + os.sep + file_name2, sock)


                for item in dict["modify_directory"]:
                    if item not in self.changes_from_server_dict["modify_directory"]:
                        send_massage("modify_directory", sock)
                        send_massage(self.client_id, sock)
                        print(item[0], item[1])

                        send_new_folder_path(item[0], item[1], self.directory, sock, self.client_id)

                for item in dict["modify"]:
                    if item not in self.changes_from_server_dict["modify"]:
                        send_massage("modify", sock)
                        send_massage(self.client_id, sock)
                        delete_path = item.replace(self.directory, "")
                        send_massage(os.path.join(self.client_id, delete_path), sock)
                        folder_name, file_name = names(self.directory, item)
                        send_a_single_file(item, file_name, os.sep + self.client_id, folder_name, sock)

                for item in dict["delete"]:
                    if item not in self.changes_from_server_dict["delete"]:
                        send_massage("delete", sock)
                        send_massage(self.client_id, sock)
                        send_massage(item, sock)

                self.handler.set_list_empty()
                if flag_erease_dict != 1:
                    for key in self.changes_from_server_dict:
                        self.changes_from_server_dict[key] = []

                send_massage("no more changes", sock)


        except:
            self.observer.stop()
        self.observer.join()

        print("\nWatcher Terminated\n")


class MyHandler(FileSystemEventHandler):

    def __init__(self, ip, port, sock, client_id, path_folder_client):
        FileSystemEventHandler.__init__(self)
        self.dict_change = {"delete": [], "create": [], "create_directory": [], "rename_file": [],
                            "modify_directory": [], "modify": []}
        self.socket = sock
        self.ip = ip
        self.port = port
        self.client_id = client_id
        self.path_folder_client = path_folder_client
        self.flag_create_file = 0
        self.flag_create_folder = 0
        self.flag_rename_folder = 0
        self.flag_rename_file = 0

    def set_list_empty(self):
        for key in self.dict_change:
            self.dict_change[key] = []

    def get_dict(self):
        return self.dict_change

    def close_socket(self):
        self.socket.close()

    def set_socket(self, sock):
        self.socket = sock

    # create file
    def on_created(self, event):
        print(f"hey buddy, {event.src_path} has been create")
        if event.is_directory:
            # self.flag_create_folder = 1
            self.dict_change["create_directory"].append(event.src_path)
        else:
            self.flag_create_file = 1
            self.dict_change["create"].append(event.src_path)

    def on_deleted(self, event):
        print("delete")
        str = event.src_path.replace(self.path_folder_client, "")
        print(str)
        self.dict_change["delete"].append(self.client_id + str)

    def on_modified(self, event):
        print(f"hey buddy, {event.src_path} has been modified")
        self.flag_rename_folder = 0
        if not event.is_directory:
            if self.flag_create_file == 0 and self.flag_rename_file == 0:
                self.dict_change["modify"].append(event.src_path)
            self.flag_rename_file = 0

    def on_moved(self, event):
        print("move")
        if event.is_directory:
            if self.flag_rename_folder == 0:
                self.flag_rename_folder = 1
                self.dict_change["modify_directory"].append([event.src_path, event.dest_path])
        else:
            # if the name of the file was changed, and the file didn't only move
            dest_path_arr = event.dest_path.split(os.sep)
            src_path_arr = event.src_path.split(os.sep)
            lenn = len(src_path_arr)
            if src_path_arr[lenn - 1] != dest_path_arr[lenn - 1]:
                print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")
                self.dict_change["rename_file"].append([event.src_path, event.dest_path])
                self.flag_rename_file = 1
