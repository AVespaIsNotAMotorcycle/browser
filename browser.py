def file_scheme(path):
    import os
    headers = {}
    print(path)
    body = open(path).read()
    return headers, body

def socket_connection(s, host, port, path):
    s.connect((host, port))
    s.send("GET {} HTTP/1.1\r\n".format(path).encode("utf8") +
           "Host: {}\r\n".format(host).encode("utf8") +
           "Connection: {}\r\n".format("close").encode("utf8") +
           "User-Agent: {}\r\n\r\n".format("avinam").encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
    
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers
    
    body = response.read()
    s.close()
    return headers, body

def http_scheme(host, path):
    import socket
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    port = 80
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)
    return socket_connection(s, host, port, path)

def https_scheme(host, path):
    port = 443
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)
   
    import socket
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    import ssl
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(s, server_hostname=host)
    return socket_connection(s, host, port, path)

def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https", "file"], \
        "Unknown scheme {}".format(scheme)
    host, path = url.split("/", 1)
    path = "/" + path
    if scheme == "file":
        return file_scheme(path)
    if scheme == "http":
        return http_scheme(host, path)
    if scheme == "https":
        return https_scheme(host, path)

def show(body):
  in_angle = False
  for c in body:
      if c == "<":
          in_angle = True
      elif c == ">":
          in_angle = False
      elif not in_angle:
          print(c, end="")

def load(url):
    headers, body = request(url)
    show(body)

if __name__ == "__main__":
    import sys
    load(sys.argv[1])
