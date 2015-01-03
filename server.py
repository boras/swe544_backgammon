import socket
import threading
from threading import Timer
from threading import Event
from backgammonlib import *
import os
import time
import Queue
import select
import select

# Global Variables
# userList is the server-wide list of users userList is accessed by different threads
# Therefore, userListLock must be obtained before accessing it
userList = {}
userListLock = threading.Lock()
clientPongWinOpen = False
commServerAddr='./CommServer_uds_socket'

class CommServer(threading.Thread):
        """
        TODO: purpose of the class
        """

        def __init__(self, queue, nofActiveUsers, serverAddr=commServerAddr):
                """
                TODO: purpose of the method
                """
                threading.Thread.__init__(self)
                self.queue = queue
                self.nofActiveUsers = nofActiveUsers
                self.serverAddr = serverAddr
                self.serverUdsSock = -1

        def setup(self):
                """
                TODO: purpose of the method
                """
                # Make sure the socket does not already exist
                try:
                        os.unlink(self.serverAddr)
                except OSError:
                        if os.path.exists(self.serverAddr):
                                raise
                # Create a UDS socket
                try:
                        self.serverUdsSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        self.serverUdsSock.bind(self.serverAddr)
                        self.serverUdsSock.listen(self.nofActiveUsers)
                        #self.serverUdsSock.setblocking(0) # non-blocking socket
                except socket.error as err:
                        print(err)
                        if self.serverUdsSock != -1:
                                self.serverUdsSock.close()
                        return False
                return True

        def run(self):
                """
                TODO: purpose of the method
                """
                if self.setup() is False:
                        print('CommServer setup() failed')
                        return
                while True:
                        userUdsSock, userAddr = self.serverUdsSock.accept()
                        username = userUdsSock.recv(64)
                        print('CommServer: ', username)
                        self.queue.put((username, userUdsSock))

class Heartbeat(threading.Thread):
        """
        Representation of a backgammon user
        """

        def __init__(self, queue, heartbeat=10, backtobackMissingCount=2, delayTime=2):
                """
                TODO: purpose of the method
                """
                threading.Thread.__init__(self)
                self.queue = queue
                self.heartbeat = heartbeat
                self.backtobackMissingCount = backtobackMissingCount
                self.delayTime = delayTime
                self.sleepTime = 1
                self.remainingTime = 0

        def sendHeartbeatMsg(self):
                """
                TODO: purpose of the method
                """
                msg = createPingMsg()
                # TODO: userList is global and needs locking
                userListLock.acquire()
                for user in userList:
                        s = userList[user][0].getUserSock()
                        print('sendHeartbeatMsg to ' + str(userList[user][0]))
                        try:
                                s.send(msg)
                        except socket.error as err:
                                #print(msg)
                                #print(err)
                                pass
                userListLock.release()

        def run(self):
                """
                TODO: purpose of the method
                """
                while True:
                        time.sleep(self.sleepTime)
                        self.remainingTime += self.sleepTime
                        # check if a new user connected to the server
                        try:
                                userInfo = self.queue.get(False)
                                print('Heartbeat: ', userInfo)
                                username = userInfo[0]
                                udsSock = userInfo[1]
                                #udsSock.send('msg from Heartbeat to ' + username)
                                userListLock.acquire()
                                userList[username].append(udsSock)
                                event = userList[username][0].getEvent()
                                event.set()
                                userListLock.release()
                        except Queue.Empty:
                                pass
                        # Check 30 seconds expired (approximately)
                        if self.remainingTime >= self.heartbeat:
                                global clientPongWinOpen
                                self.remainingTime = 0
                                self.sendHeartbeatMsg()
                                self.checkTimer = Timer(self.delayTime, self.checkUsers)
                                clientPongWinOpen = True
                                self.checkTimer.start()

        def checkUsers(self):
                """
                TODO: purpose of the method
                """
                global clientPongWinOpen
                clientPongWinOpen = False

                userListLock.acquire()
                for userEntry in userList:
                        user = userList[userEntry][0]
                        try:
                                udsSock = userList[userEntry][1]
                                if user.update_pongMissingCount() ==self.backtobackMissingCount:
                                        udsSock.send('dead')
                                print('checkUsers: ' + user.username + ": "
                                      + str(user.getMissingCount()))
                        except IndexError:
                                # Heartbeat hasn't had a chance to append it to
                                # userList entry yet. Don't check that user
                                pass
                userListLock.release()

class User(threading.Thread):
        """
        Representation of a backgammon user
        """

        def __init__(self, csock, addr, heartbeat, serverAddr=commServerAddr):
                """
                TODO: purpose of the method
                """
                threading.Thread.__init__(self)
                self.userSock = csock
                self.addr = addr
                self.heartbeat = heartbeat
                self.serverAddr = serverAddr
                self.userUdsSock =-1
                self.userType = 'unknown'
                self.username = 'unknown'
                self.event = Event()
                self.pongMissingCount = 0
                self.poller = -1
                self.fdToSocket = {}

        def connectToCommServer(self):
                """
                TODO: purpose of the method
                """
                self.userUdsSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.userUdsSock.connect(self.serverAddr)
                self.userUdsSock.send(self.username)
                #msg = self.userUdsSock.recv(128)
                #print('importante: ' + str(msg))
                # Sync with Heartbeat before going further
                self.event.wait()

        def run(self):
                """
                TODO: purpose of the method
                """
                print('Got connection from', self.addr)
                msg = self.userSock.recv(1024)
                print(msg)
                #print(handleLoginRequest(msg))
                self.username = self.handleLoginRequest(msg)
                userListLock.acquire()
                if userList.get(self.username) is None:
                        userEntry = []
                        userEntry.append(self)
                        userList[self.username] = userEntry
                        self.state = 'CONNECTED'
                        print('OK: ' + str(self.username) +
                              '. You are logged in to the server')
                        result = True
                else:
                        print('FAIL: ' + str(self.username) + ' already exists.')
                        result = False
                userListLock.release()
                self.userSock.send(self.sendLoginResponse(result))
                if result is False:
                        self.userSock.close()
                        return

                # Connect to CommServer and send username
                self.connectToCommServer()

                # TODO: select for unix domain socket and client socket
                READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
                self.poller = select.poll()
                self.fdToSocket[self.userSock.fileno()] = self.userSock
                self.fdToSocket[self.userUdsSock.fileno()] = self.userUdsSock
                self.poller.register(self.userSock, READ_ONLY)
                self.poller.register(self.userUdsSock, READ_ONLY)
                out = False
                while True:
                        events = self.poller.poll()
                        for fd, flag in events:
                                s = self.fdToSocket[fd]
                                if flag & (select.POLLIN | select.POLLPRI):
                                        if s is self.userUdsSock:
                                                msg = self.userUdsSock.recv(128)
                                                if msg == 'dead':
                                                        print(self.username + ' is dead')
                                                        userListLock.acquire()
                                                        u = userList.pop(self.username, None)
                                                        if u is None:
                                                                print(self.username +
                                                                      'is not in userList')
                                                        userListLock.release()
                                                        out = True
                                                        break
                                        if s is self.userSock:
                                                self.handleUserMsg()
                        if out is True:
                                break

                # cleanup
                for entry in self.fdToSocket:
                        sock = self.fdToSocket[entry]
                        self.poller.unregister(sock)
                self.userSock.close()
                self.userUdsSock.close()

        def handleUserMsg(self):
                """
                TODO: purpose of the method
                """
                rMsg = self.userSock.recv(1024)
                #print('handleUserMsg: ', rMsg)
                header = getMsgHeader(rMsg)
                if header == 'CLPONG':
                        self.handlePongResponse()
                elif header == '':
                        self.poller.unregister(self.userSock)
                        self.fdToSocket.pop(self.userSock.fileno())
                else:
                        print(rMsg)
                        sMsg = createSvrnokMsg()
                        print(sMsg)
                        self.userSock.send(sMsg)

        def handlePongResponse(self):
                """
                TODO: purpose of the method
                """
                global clientPongWinOpen
                if clientPongWinOpen is True:
                        self.pongMissingCount = -1

        def update_pongMissingCount(self):
                """
                TODO: purpose of the method
                """
                self.pongMissingCount += 1
                return self.pongMissingCount

        def getMissingCount(self):
                """
                TODO: purpose of the method
                """
                return self.pongMissingCount

        def getUserSock(self):
                """
                TODO: purpose of the method
                """
                return self.userSock

        def getEvent(self):
                """
                TODO: purpose of the method
                """
                return self.event

        def handleLoginRequest(self, message):
                """
                TODO: purpose of the method
                """

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
                """
                TODO: purpose of the method
                """
                if result is False:
                        msg = createLoginResponseMsg("fail")
                else:
                        msg = createLoginResponseMsg("success")
                return msg

        def __str__(self):
                """
                TODO: purpose of the method
                """
                return self.username

class Server(object):
        """
        Representation of a simple backgammon server
        """

        def __init__(self, port=10001, nofActiveUsers=1000):
                """
                Initialize server instance
                """
                self.port = port
                self.nofActiveUsers = nofActiveUsers

        def setupSocket(self):
                """
                TODO: purpose of the method
                """
                self.s = socket.socket()
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.host = socket.gethostname()
                print('Server IP address: ' + self.host + ' and port: ' + str(self.port))
                self.s.bind((self.host, self.port))
                self.s.listen(self.nofActiveUsers)

        def setupThreading(self):
                """
                TODO: purpose of the method
                """
                self.queue = Queue.Queue()
                self.CommServer = CommServer(self.queue, self.nofActiveUsers)
                self.CommServer.start()
                self.heartbeat = Heartbeat(self.queue)
                self.heartbeat.start()

        def setup(self):
                """
                TODO: purpose of the method
                """
                self.setupSocket()
                self.setupThreading()

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
                self.CommServer.join()
                # TODO: destroy self.queue is needed?

        def __str__(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

if __name__ == "__main__":
        s = Server()
        s.run()
