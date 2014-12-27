import socket

s = socket.socket()
host = socket.gethostname()
port = 10001
print('My IP address: ' + host)
s.bind((host, port))
s.listen(5)

while True:
        c, addr = s.accept()
        print('Got connection from', addr)
        c.send('Thank you for connection!')
        print c.recv(1024)
        c.close()
