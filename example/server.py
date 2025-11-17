import socketserver

class CCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()

        print(f"Data recived from {self.client_address}: {self.data}")

if __name__ == '__main__':
    HOST, PORT = "localhost", 9090

    cc = socketserver.TCPServer((HOST, PORT), CCHandler)
    cc.serve_forever()