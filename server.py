import socket
import select  # Yes, we're using select for multiple clients
import json  # To send multiple data without 10 billion commands

from utils import receive_message, removeprefix, make_header


class HiSockServer:
    class _on:
        """Decorator used to handle something when receiving command"""
        def __init__(self, outer, cmd_activation):
            self.outer = outer
            self.cmd_activation = cmd_activation

        def __call__(self, func):
            def inner_func(*args, **kwargs):
                ret = func(*args, **kwargs)
                return ret

            self.outer.funcs[self.cmd_activation] = func
            return inner_func

    def __init__(self, addr, max_connections=0, header_len=16):
        self.addr = addr
        self.header_len = header_len

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)
        self.sock.bind(addr)
        self.sock.listen(max_connections)

        self.funcs = {}

        self._sockets_list = [self.sock]
        self.clients = {}
        self.clients_rev = {}

    def on(self, something):
        return HiSockServer._on(self, something)

    def send_all_clients(self, command: str, content: bytes):
        content_header = make_header(command.encode() + b" " + content, self.header_len)
        for client in self.clients:
            client.send(
                content_header + command.encode() + b" " + content
            )

    def run(self):
        read_sock, write_sock, exception_sock = select.select(self._sockets_list, [], self._sockets_list)

        for notified_sock in read_sock:
            if notified_sock == self.sock:  # Got new connection
                connection, address = self.sock.accept()
                client = receive_message(connection, self.header_len)

                client_hello = removeprefix(client['data'].decode(), "$CLTHELLO$ ")
                client_hello = json.loads(client_hello)

                print(client_hello)  # DEBUG PRINT - REMEMBER TO REMOVE
                self._sockets_list.append(connection)
                self.clients[connection] = {
                    "ip": address,
                    "name": client_hello['name'],
                    "group": client_hello['group']
                }
                self.clients_rev[(
                    address,
                    client_hello['name'],
                    client_hello['group']
                )] = connection

                if 'join' in self.funcs:
                    # Reserved function
                    self.funcs['join'](
                        {
                            "ip": address,
                            "name": client_hello['name'],
                            "group": client_hello['group']
                        }
                    )


if __name__ == "__main__":
    s = HiSockServer(('192.168.1.131', 33333))

    @s.on("join")
    def test_sussus(yum_data):
        print("Sussus amogus, function successfully called by HiSock class")
        print(yum_data)
        s.send_all_clients("Joe", b"Bidome")

    while True:
        s.run()
