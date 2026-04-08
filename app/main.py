import gzip
import socket  # noqa: F401
import sys
import threading


class Request:
    def __init__(self, data: bytes):
        data = data.decode()
        lines = data.split("\r\n")
        request_line = lines[0].split(" ")
        if len(request_line) != 3:
            raise ValueError(f"Invalid HTTP request line: {lines[0]!r}")
        self.method, self.path, self.http_version = request_line
        self.headers = {}

        for line in lines[1:]:
            if not line:
                break
            key, value = line.split(": ", 1)
            self.headers[key] = value
        
        self.separator = "\r\n\r\n"
        body_start = data.find(self.separator)
        self.body = data[body_start + len(self.separator):] if body_start != -1 else ""
    
    def handle_request(self) -> bytes:
        response_status = "HTTP/1.1 404 Not Found"
        response_headers = {}
        response_body: str | bytes = ""
        
        if self.method == 'GET':
            if self.path == '/':
                response_status = "HTTP/1.1 200 OK"
            elif self.path.startswith('/echo/') and len(self.path.split('/')) == 3:
                response_status = "HTTP/1.1 200 OK"
                response_body = self.path.split('/')[-1]
                response_headers["Content-Type"] = "text/plain"
            elif self.path == '/user-agent':
                response_status = "HTTP/1.1 200 OK"
                response_body = self.headers.get("User-Agent", "")
                response_headers["Content-Type"] = "text/plain"
            elif self.path.startswith('/files/') and len(self.path.split('/')) == 3:
                filename = self.path.split('/')[-1]
                response_status, response_headers, response_body = self._read_file(filename)
        elif self.method == 'POST':
            if self.path.startswith('/files/') and len(self.path.split('/')) == 3:
                filename = self.path.split('/')[-1]
                response_status, response_headers, response_body = self._create_file(filename)
        
        # Compression headers
        if self.headers.get("Accept-Encoding"):
            compression_schemes = self.headers.get("Accept-Encoding").split(', ')
            for scheme in compression_schemes:
                if scheme in ['gzip']:
                    response_headers["Content-Encoding"] = 'gzip'
                    response_body = gzip.compress(response_body.encode())
                    break

        return self._build_response(response_status, response_headers, response_body)

    def _build_response(self, status: str, headers: dict[str, str], body: str | bytes = "") -> bytes:
        response_headers = headers.copy()
        body_bytes = body.encode() if isinstance(body, str) else body
        response_headers["Content-Length"] = str(len(body_bytes))

        header_lines = "".join(
            f"{key}: {value}\r\n" for key, value in response_headers.items()
        )
        response = f"{status}\r\n{header_lines}\r\n".encode()
        return response + body_bytes

    def _read_file(self, filename: str) -> tuple[str, dict[str, str], str]:
        filepath = f"{sys.argv[2]}/{filename}"
        try:
            with open(filepath, "rb") as file:
                content = file.read()
        except FileNotFoundError:
            return "HTTP/1.1 404 Not Found", {}, ""

        return "HTTP/1.1 200 OK", {
            "Content-Type": "application/octet-stream",
        }, content.decode()

    def _create_file(self, filename: str) -> tuple[str, dict[str, str], str]:
        filepath = f"{sys.argv[2]}/{filename}"
        with open(filepath, "wb") as file:
            file.write(self.body.encode())
        return "HTTP/1.1 201 Created", {}, ""


def handle_client(conn, address):
    with conn:
        print(f"accepted connection from {address}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
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
