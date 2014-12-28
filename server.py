import socket
from threading import Timer
from backgammonlib import *

#userList = {}
#clientSocketList = []
heartbeat = 10.0

def sendHeartbeatMsg():
        print("heartbeat")
        #t = Timer(heartbeat, sendHeartbeatMsg)
        #t.start()

#t = Timer(heartbeat, sendHeartbeatMsg)
#t.start()

#s = socket.socket()
#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#host = socket.gethostname()
#port = 10001
#print('My IP address: ' + host)
#s.bind((host, port))
#s.listen(5)

#while True:
        #c, addr = s.accept()
        #print('Got connection from', addr)
        ##c.send('Thank you for connection!')
        #msg = c.recv(1024)
        #print(msg)
        ##print(handleLoginRequest(msg))
        #result, username = handleLoginRequest(msg)
        #if result is False:
                #print('FAIL: ' + str(username) + ' already exists. Choose another username')
        #else:
                #print('OK: ' + str(username) + '. You are logged in to the server')
        #c.send(sendLoginResponse(result))
        ##c.close()


class Server(object):
        """
        Representation of a simple backgammon server
        """
        def __init__(self, port=10001, backlog=5):
                """
                Initialize server instance
                """
                self.port = port
                self.backlog = backlog
                self.userList = {}
                self.waitingList = {}
                self.clientSocketList = []

        def setup(self):
                """
                TODO: purpose of the method
                """
                self.s = socket.socket()
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.host = socket.gethostname()
                print('My IP address: ' + self.host + ' and port: ' + str(self.port))
                self.s.bind((self.host, self.port))
                self.s.listen(self.backlog)

        def run(self):
                """
                TODO: purpose of the method
                """
                self.setup()
                while True:
                        c, addr = self.s.accept()
                        print('Got connection from', addr)
                        #c.send('Thank you for connection!')
                        msg = c.recv(1024)
                        print(msg)
                        #print(handleLoginRequest(msg))
                        result, username = self.handleLoginRequest(msg)
                        if result is False:
                                print('FAIL: ' + str(username) + ' already exists. Choose another username')
                        else:
                                print('OK: ' + str(username) + '. You are logged in to the server')
                        c.send(self.sendLoginResponse(result))
                        #c.close()

        def checkUsername(self, username):
                """
                """
                return True

        def handleLoginRequest(self, message):
                #print(message)
                #print("=======")
                userEntry = []
                msg = message
                msgList = msg.split('\n')
                if msgList[0] != 'CLOGIN':
                        return
                msgList = msgList[3].split(':')
                key = msgList[0].split('"')[1]
                if key != 'userid':
                        return
                username = msgList[1].split('"')[1]
                #print(username)
                if self.userList.get(username) is None and self.checkUsername(username):
                        userEntry.append(username)
                        self.userList[username] = 'CONNECTED'
                        return True, username
                return False, username

        def sendLoginResponse(self, result):
                if result is False:
                        msg = createLoginResponseMsg("fail")
                else:
                        msg = createLoginResponseMsg("success")
                return msg

        def __str__(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

if __name__ == "__main__":
        s = Server()
        s.run()
