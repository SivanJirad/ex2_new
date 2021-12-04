import socket
import os
import sys
import utils

BUFFER_SIZE = 4096


def create_id_and_folder_client(path):
    client_id = utils.create_id()
    new_client_path = os.path.join(path, client_id)
    # crete new folder to client
    if not os.path.exists(new_client_path):
        os.makedirs(new_client_path)
    byte_message = bytes(client_id, 'utf-8')
    # send to client id
    client_socket.send(byte_message)
    return client_id


def search_folder_and_push_to_client(id_file_name, path, socket):
    for root, dir, files in os.walk(path):
        for folder in dir:
            # finding the client folder by his id
            if folder == id_file_name:
                path = os.path.join(path, id_file_name)
                utils.push_all_folders(path, '', socket)
                utils.send_massage("done", socket)
                utils.push_all_files(path, '', socket)
                socket.send(b'it is last')
                break


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_id_of_client():
    #   client_socket.send(b'got it')
    id_c = client_socket.recv(BUFFER_SIZE).decode("utf-8")
    #    client_socket.send(b'got it')
    return id_c


def delete_client_id_in_the_path(path):
    parts_of_path = path.decode("utf-8").split(os.sep)
    new_path2 = parts_of_path[1]
    for i in range(2, len(parts_of_path) - 1):
        new_path2 = os.path.join(new_path2, parts_of_path[i])
    return new_path2


def update_data_dict(computer_id, all_computer_id, place, data_to_send, computer_id_dict):
    for client_computer_id in all_computer_id:
        # update the dictionary of all the different computers except for this one
        if client_computer_id != computer_id:
            computer_id_dict[client_computer_id][place].append(data_to_send)


if __name__ == '__main__':
    new_path = os.path.join(os.getcwd(), "Server")
    # create new folder to sever
    make_folder(new_path)

    id_dict = {}
    computer_id_dict = {}

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', int(sys.argv[1])))
    server.listen(5)

    while True:
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        computer_id = utils.rec_massage(client_socket).decode("utf-8")


        first_data = client_socket.recv(BUFFER_SIZE)

        if first_data == b'hello':
            # new client without id, server create id and open folder to save client's files"
            id_client = create_id_and_folder_client(new_path)
            # sever pull all folder from client
            utils.pull_all_folders(new_path, client_socket)
            utils.pull_all_files(new_path + os.sep, client_socket)

            id_dict.update({id_client: [computer_id]})
            save_data_dict = {"delete": [], "create": [], "create_directory": [], "rename_file": [],
                              "modify_directory": [], "modify": []}
            computer_id_dict.update({computer_id: save_data_dict})

        elif first_data == b'already know you':
            client_socket.send(b'got it')
            data = client_socket.recv(BUFFER_SIZE)
            client_id = data.decode("utf-8")
            search_folder_and_push_to_client(client_id, new_path, client_socket)
            id_dict[client_id].append(computer_id)
            save_data_dict = {"delete": [], "create": [], "create_directory": [], "rename_file": [],
                              "modify_directory": [], "modify": []}
            computer_id_dict.update({computer_id: save_data_dict})

        # updating and getting updates from the client
        else:
            client_id = first_data.decode("utf-8")
            changes_dict = computer_id_dict[computer_id]
            for change in changes_dict:
                all_data = changes_dict[change]

                if change == 'create_directory' and changes_dict[change] != []:
                    utils.send_massage(change, client_socket)
                    for data_to_send in changes_dict[change]:
                        str_data = data_to_send.decode("utf-8").replace(client_id + os.sep, '')
                        client_socket.send(bytes(str_data, "utf-8"))

                if change == 'create' and changes_dict[change] != []:
                    utils.send_massage(change, client_socket)
                    for data_to_send in changes_dict[change]:
                        folder_name, file_name = utils.names(client_id, data_to_send.decode("utf-8"))
                        #print(new_path + os.sep + data_to_send.decode("utf-8"))
                        utils.send_a_single_file(new_path + os.sep + data_to_send.decode("utf-8"),
                                                 file_name, '', folder_name, client_socket)

                if change == 'delete' and changes_dict[change] != []:
                    utils.send_massage(change, client_socket)
                    for data_to_send in changes_dict[change]:
                        # print(delete_client_id_in_the_path(data_to_send))
                        str_data = data_to_send.decode("utf-8").replace(client_id + os.sep, '')
                        utils.send_massage(str_data, client_socket)


                if (change == 'rename_file' or change == 'modify_directory') and changes_dict[change] != []:
                    utils.send_massage(change, client_socket)
                    for data_to_send in changes_dict[change]:
                        str_src_data = data_to_send[0].decode("utf-8").replace(client_id + os.sep, '')
                        utils.send_massage(str_src_data, client_socket)
                        str_dest_data = data_to_send[1].decode("utf-8").replace(client_id + os.sep, '')
                        utils.send_massage(str_dest_data, client_socket)


                if change == 'modify' and changes_dict[change] != []:
                    utils.send_massage(change, client_socket)
                    for data_to_send in changes_dict[change]:
                        str_data = data_to_send[0].decode("utf-8").replace(os.sep + client_id + os.sep, '')
                        utils.send_massage(str_data, client_socket)
                        folder_name, file_name = utils.names(client_id, data_to_send[1].decode("utf-8"))
                        # print(new_path + os.sep + data_to_send.decode("utf-8"))
                        utils.send_a_single_file(new_path + os.sep + data_to_send[1].decode("utf-8"),
                                                 file_name, '', folder_name, client_socket)
            utils.send_massage("do nothing", client_socket)

            # earase all the changes we did
            for key in computer_id_dict[computer_id]:
                computer_id_dict[computer_id][key] = []

            data = client_socket.recv(utils.BUFFER_SIZE)
            print(data)

            while data != b'no more changes':
                if data == b'create':
                    client_socket.send(b'got it')
                    client_id = get_id_of_client()
                    print(client_id)
                    client_socket.send(b'got it')
                    data2 = client_socket.recv(utils.BUFFER_SIZE)
                    print(data2)
                    utils.get_a_single_file(new_path, client_socket, data2)
                    all_computer_id = id_dict[client_id]
                    update_data_dict(computer_id, id_dict[client_id], "create", data2, computer_id_dict)

                elif data == b'delete':
                    client_socket.send(b'got it')
                    client_id = get_id_of_client()
                    print(client_id)
                    client_socket.send(b'got it')
                    data2 = utils.rec_massage(client_socket)
                    print(data2)
                    utils.delete_a_single_file_or_folder(new_path, data2.decode("utf-8"))
                    all_computer_id = id_dict[client_id]
                    update_data_dict(computer_id, all_computer_id, "delete", data2, computer_id_dict)

                elif data == b'modify':
                    client_socket.send(b'got it')
                    client_id = get_id_of_client()
                    client_socket.send(b'got it')
                    data_to_delete = client_socket.recv(utils.BUFFER_SIZE)
                    print(data_to_delete)
                    utils.delete_a_single_file_or_folder(new_path, data_to_delete.decode("utf-8"))
                    client_socket.send(b'got it')
                    data_to_create = client_socket.recv(utils.BUFFER_SIZE)
                    utils.get_a_single_file(new_path, client_socket, data_to_create)
                    all_computer_id = id_dict[client_id]
                    update_data_dict(computer_id, all_computer_id, "modify", [data_to_delete, data_to_create],
                                     computer_id_dict)

                elif data == b'create_directory':
                    client_socket.send(b'got it')
                    client_id = get_id_of_client()
                    client_socket.send(b'got it')
                    data2 = client_socket.recv(utils.BUFFER_SIZE)
                    path = os.path.join(new_path, data2.decode("utf-8"))
                    make_folder(path)
                    all_computer_id = id_dict[client_id]
                    update_data_dict(computer_id, all_computer_id, "create_directory", data2, computer_id_dict)

                elif data == b'rename_file' or data == b'modify_directory':
                    client_socket.send(b'got it')
                    client_id = get_id_of_client()
                    client_socket.send(b'got it')
                    data1 = utils.rec_massage(client_socket)
                    src_path = os.path.join(new_path, data1.decode("utf-8"))
                    data2 = utils.rec_massage(client_socket)
                    dest_path = os.path.join(new_path, data2.decode("utf-8"))
                    os.rename(src_path, dest_path)
                    all_computer_id = id_dict[client_id]
                    update_data_dict(computer_id, all_computer_id, data.decode("utf-8"), [data1, data2],
                                     computer_id_dict)

                data = utils.rec_massage(client_socket)


        print(id_dict)
        print(computer_id_dict)

        client_socket.close()
        print('Client disconnected')