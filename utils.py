import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('www.google.com', 80))

    ip, _ = s.getsockname()
    s.close()

    return ip