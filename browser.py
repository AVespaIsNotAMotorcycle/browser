def file_scheme(path):
    import os
    headers = {}
    body = open(path).read()
    return headers, body

def socket_connection(s, host, port, path):
    s.connect((host, port))
    s.send("GET {} HTTP/1.1\r\n".format(path).encode("utf8") +
           "Host: {}\r\n".format(host).encode("utf8") +
           "Connection: {}\r\n".format("close").encode("utf8") +
           "User-Agent: {}\r\n".format("avinam").encode("utf8") +
           "Accept-Encoding: {}\r\n\r\n".format("gzip").encode("utf8"))
    response = s.makefile("rb", newline="\r\n")
    header_strs = []
    body_bytes = []
    in_body = False
    for line in response:
        if not in_body:
            if (line.decode("utf8") == "\r\n"):
                in_body = True
            else:
                header_strs.append(line.decode("utf8"))
        else:
            body_bytes.append(line)
    statusline = header_strs[0]
    header_strs = header_strs[1:]
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    for line in header_strs:
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
   
    body = b''.join(body_bytes)
    if "transfer-encoding" in headers:
        body = b''
        in_chunk = False
        chunk_full_len = 0
        chunk_curr_len = 0
        for chunk in body_bytes:
            if chunk_curr_len >= chunk_full_len:
                in_chunk = False
            if not in_chunk:
                if chunk[-2:] == b'\r\n':
                    in_chunk = True
                    chunk_full_len = int(chunk[:-2], 16)
                    if chunk_full_len == 0:
                        break
            else:
                body += chunk
                chunk_curr_len += len(chunk)
        #print("TRANSFER-ENCODING")
        while body[-2:] == b'\r\n':
            body = body[:-2]
    if "content-encoding" in headers:
        import gzip
        body = gzip.decompress(body)
    body = body.decode("utf8")
 
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

def data_scheme(path):
    headers = {}
    body = path
    if path[:6] == "/html,":
        body = path[6:]
    return headers, body

def parse_scheme_and_url(url):
    if url[:5] == "data:":
        return url[:4], url[5:]
    if url[:11] == "view-source":
        return url[:11], url[12:]
    scheme, url = url.split("://", 1)
    return scheme, url

def view_source_scheme(url):
    headers, body = request(url)
    body = body.replace("<", "&lt;")
    body = body.replace(">", "&gt;")
    return headers, body

def request(url):
    scheme, url = parse_scheme_and_url(url)
    assert scheme in ["http", "https", "file", "data", "view-source"], \
        "Unknown scheme {}".format(scheme)
    host, path = url.split("/", 1)
    path = "/" + path
    if scheme == "file":
        return file_scheme(path)
    if scheme == "data":
        return data_scheme(path)
    if scheme == "http":
        return http_scheme(host, path)
    if scheme == "https":
        return https_scheme(host, path)
    if scheme == "view-source":
        return view_source_scheme(url)

def remove_entities(text):
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", "\"")
    text = text.replace("&amp;", "&")
    return text

def render_html(html):
    in_angle = False
    tag_name = ""
    in_body = False
    text = ""
    for c in html:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
            if tag_name == "body":
                in_body = True
            if tag_name == "/body":
                in_body = False
            tag_name = ""
        elif not in_angle:
            if in_body:
                text += c
        elif c != "\n":
            tag_name += c
    text = remove_entities(text)
    return text

def show(body):
    if body.find("<html") != -1:
        print(render_html(body))
        return
    print(remove_entities(body))

def load(url):
    headers, body = request(url)
    show(body)

if __name__ == "__main__":
    import sys
    load(sys.argv[1])
