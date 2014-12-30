import socket
import threading
from threading import Timer
from threading import Event
from backgammonlib import *
import os
import time
import select

userList = {}
#clientSocketList = []
heartbeat = 10.0

class Heartbeat(threading.Thread):
        """
        Representation of a backgammon user
        """
        def __init__(self, backtobackMissingCount=2, delayTime=5, heartbeat=30):
                """
                TODO: purpose of the method
                """
                threading.Thread.__init__(self)
                self.heartbeat = heartbeat
                self.backtobackMissingCount = backtobackMissingCount
                self.delayTime = delayTime
                self.sleepTime = 1
                self.remainingTime = 0
                self.serverAddr = './heartbeat_uds_socket'
                self.userList = {}
                self.udsSock = -1

        def setup(self):
                # Make sure the socket does not already exist
                try:
                        os.unlink(self.serverAddr)
                except OSError:
                        if os.path.exists(self.serverAddr):
                                raise
                # Create a UDS socket
                try:
                        self.udsSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        self.udsSock.bind(self.serverAddr)
                        self.udsSock.listen(10)
                        #self.udsSock.setblocking(0)
                except socket.error as msg:
                        print(msg)
                        self.udsSock.close()
                        return False
                return True

        def run(self):
                print('Heartbeat object')
                if self.setup() is False:
                        return False
                while True:
                        sleep(self.sleepTime)
                        self.remainingTime += self.sleepTime
                        if self.remainingTime >= self.heartbeat:
                                self.remainingTime = 0
                connection, client_address = self.udsSock.accept()
                msg = connection.recv(16)
                print(msg)

        def checkUsers(self):
                count = self.backtobackMissingCount
                informedUsers = {}
                for userEntry in userList:
                        # user pinged
                        if userEntry[1] == -1:
                                userEntry[1] = 0
                        else:
                                userEntry[1] += 1
                        if userEntry[1] == count:
                                informedUsers[userEntry[0]] = 'dead'

        #def addUser(self, username, userObject):
                #print('addUser')
                #userEntry = []
                #count = 0
                #userEntry.append(userObject)
                #userEntry.append(count)
                ##time = self.remainingTime + self.delayTime
                ##t = Timer(time, self.checkUsers)
                ##userEntry.append(t)
                ##t.start()
                ##self.userList[username] = userEntry

        #def wakeUp(self, username):
                #print('wakeUp')

        def ping(self, username):
                userEntry = self.userList[username]
                userEntry[1] = -1

def sendHeartbeatMsg():
        #print("heartbeat")
        msg = createHeartbeatMsg()
        #print(msg)
        for user in userList:
                userList[user].s.send(msg)
        t = Timer(heartbeat, sendHeartbeatMsg)
        t.start()

t = Timer(heartbeat, sendHeartbeatMsg)
t.start()

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


class User(threading.Thread):
        """
        Representation of a backgammon user
        """
        def __init__(self, csock, addr, heartbeat):
                """
                TODO: purpose of the method
                """
                threading.Thread.__init__(self)
                self.s = csock
                self.addr = addr
                self.userType = 'unknown'
                self.username = 'unknown'
                self.event = Event()
                self.heartbeat = heartbeat
                #self.serverAddr = 'server@' + username

        def run(self):
                print('Got connection from', self.addr)
                msg = self.s.recv(1024)
                print(msg)
                #print(handleLoginRequest(msg))
                self.username = self.handleLoginRequest(msg)
                if userList.get(self.username) is None:
                        #userList[self.username] = 'CONNECTED'
                        userList[self.username] = self
                        self.state = 'CONNECTED'
                        print('OK: ' + str(self.username) + '. You are logged in to the server')
                        result = True
                else:
                        print('FAIL: ' + str(self.username) + ' already exists.')
                        result = False
                self.s.send(self.sendLoginResponse(result))
                if result is False:
                        self.s.close()
                        return
                #self.setupHeartbeatSock()
                # setup timer
                # First learn the remaining time from Heartbeat and then add 5 sn
                # if CLPONG is received before timer expires, then set ping = 1
                # otherwise set it to ping = 0
                # When timer expires, check ping
                # if ping == 1, then count = 0
                # if ping == 0, then count = count + 1
                # if count == 2, then client is dead, remove it from userList and close the socket
                # terminate thread
                #self.event.wait()
                #print(self.username + " is leaving")
                #self.s.close()

                #self.createUDS()
                #connection, client_address = self.udsSock.accept()
                #self.s.recv(1024)
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect('./heartbeat_uds_socket')
                sock.send('bora geliyor')
                #self.heartbeat.addUser(self.username, self)
                #self.heartbeat.wakeUp(self.username)

                # select for unix domain socket and client socket s
                #self.s.close()

        #def createUDS(self):
                ## Make sure the socket does not already exist
                #try:
                        #os.unlink(self.serverAddr)
                #except OSError:
                        #if os.path.exists(self.serverAddr):
                                #raise
                ## Create a UDS socket
                #self.udsSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                #self.udsSock = socket.bind(serverAddr)
                #self.udsSock.listen(1)

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
                return username

        def sendLoginResponse(self, result):
                if result is False:
                        msg = createLoginResponseMsg("fail")
                else:
                        msg = createLoginResponseMsg("success")
                return msg



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
                self.heartbeat = Heartbeat()
                self.heartbeat.start()

        def run(self):
                """
                TODO: purpose of the method
                """
                self.setup()
                while True:
                        csock, addr = self.s.accept()
                        #print('Got connection from', addr)
                        u = User(csock, addr, self.heartbeat)
                        u.start()
                self.heartbeat.join()

        def __str__(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

if __name__ == "__main__":
        s = Server()
        s.run()
