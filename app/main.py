import socket  # noqa: F401
import sys
import threading


class Request:
    def __init__(self, data: bytes):
        data = data.decode()
        lines = data.split("\r\n")
        self.method, self.path, self.http_version = lines[0].split(" ")
        self.headers = {}

        for line in lines[1:]:
            if not line:
                break
            key, value = line.split(": ", 1)
            self.headers[key] = value
        
        separator = "\r\n\r\n"
        body_start = data.find(separator)
        self.body = data[body_start + len(separator):] if body_start != -1 else ""
    
    def handle_request(self) -> bytes:
        response = ''
        
        if self.method == 'GET':
            if self.path == '/':
                response = "HTTP/1.1 200 OK\r\n\r\n"
            elif self.path.startswith('/echo/') and len(self.path.split('/')) == 3:
                content = self.path.split('/')[-1]
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content)}\r\n\r\n{content}"
            elif self.path == '/user-agent':
                user_agent = self.headers.get("User-Agent", "")
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
            elif self.path.startswith('/files/') and len(self.path.split('/')) == 3:
                filename = self.path.split('/')[-1]
                response = self._read_file(filename)
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
        elif self.method == 'POST':
            if self.path.startswith('/files/') and len(self.path.split('/')) == 3:
                filename = self.path.split('/')[-1]
                response = self._create_file(filename)

        return response.encode()

    def _read_file(self, filename: str) -> str:
        filepath = f"{sys.argv[2]}/{filename}"
        try:
            with open(filepath, "rb") as file:
                content = file.read()
        except FileNotFoundError:
            return "HTTP/1.1 404 Not Found\r\n\r\n"

        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/octet-stream\r\n"
            f"Content-Length: {len(content)}\r\n\r\n"
        )
        return headers + content.decode()

    def _create_file(self, filename: str) -> str:
        filepath = f"{sys.argv[2]}/{filename}"
        with open(filepath, "wb") as file:
            file.write(self.body.encode())
        return "HTTP/1.1 201 Created\r\n\r\n"


def handle_client(conn, address):
    with conn:
        print(f"accepted connection from {address}")
        data = conn.recv(1024)
        print(f"data: {data}")
        
        request = Request(data)
        print(f"method: {request.method}")
        print(f"path: {request.path}")
        print(f"headers: {request.headers}")
        print(f"body: {request.body}")
        
        response = request.handle_request()
        conn.sendall(response)


def main():
    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:
        while True:
            conn, address = server_socket.accept()  # wait for client
            thread = threading.Thread(target=handle_client, args=(conn, address))
            thread.start()


if __name__ == "__main__":
    main()
