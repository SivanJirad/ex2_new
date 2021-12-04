import sys
import socket
import utils

BUFFER_SIZE = 4096


def connect_with_server(socket):
    # send "hello" to server, server know that it need to send new id to client
    socket.send(b'hello')
    client_id = socket.recv(128).decode("utf-8")
    print("Server sent: ", client_id)
    return client_id


def no_id(client_id, directory_path, socket):
    utils.push_all_folders(directory_path, client_id, socket)
    # The client notifies the server that has finished sending the folder names to it
    utils.send_massage("done", socket)
    utils.push_all_files(directory_path, client_id, socket)
    utils.send_massage("it is last", socket)



def with_id(client_id, directory_path, socket):
    socket.send(bytes(client_id, 'utf-8'))
    utils.pull_all_folders(directory_path, socket)
    utils.pull_all_files(directory_path, socket)


if __name__ == "__main__":
    ip = sys.argv[1]
    port = int(sys.argv[2])
    directory_path = sys.argv[3]
    time_for_connect = float(sys.argv[4])
    client_id = ''
    computer_id = utils.create_id()

    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect((ip, port))
    utils.send_massage(computer_id, socket)


    # if there are only four arguments (no ID)
    if len(sys.argv) == 5:
        client_id = connect_with_server(socket)
        no_id(client_id, directory_path, socket)
    else:
        client_id = sys.argv[5]
        utils.send_massage("already know you", socket)
        with_id(client_id, directory_path, socket)

    w = utils.Watcher(directory_path, time_for_connect, ip, port, client_id, computer_id,
                          utils.MyHandler(ip, port, socket, client_id, directory_path))
    w.run()
