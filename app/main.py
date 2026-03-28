import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    with socket.create_server(("localhost", 4221), reuse_port=True) as server_socket:
        conn, address = server_socket.accept() # wait for client
        print(f"accepted connection from {address}")
        data = conn.recv(1024)
        print(f"data: {data}")
        path = str(data, 'utf-8').split(' ')[1]
        print(f"path: {path}")
        if path == '/':
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        elif path.startswith('/echo/') and len(path.split('/')) == 3:
            content = path.split('/')[-1]
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content)}\r\n\r\n{content}"
            conn.sendall(response.encode())
        else:
            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
