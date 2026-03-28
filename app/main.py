import socket  # noqa: F401


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


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:
        conn, address = server_socket.accept()  # wait for client
        print(f"accepted connection from {address}")
        data = conn.recv(1024)
        print(f"data: {data}")
        request = Request(data)
        print(f"path: {request.path}")
        print(f"host: {request.headers.get('Host')}")
        print(f"user-agent: {request.headers.get('User-Agent')}")

        if request.path == '/':
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        elif request.path.startswith('/echo/') and len(request.path.split('/')) == 3:
            content = request.path.split('/')[-1]
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content)}\r\n\r\n{content}"
            conn.sendall(response.encode())
        elif request.path == '/user-agent':
            user_agent = request.headers.get("User-Agent", "")
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
            conn.sendall(response.encode())
        else:
            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
