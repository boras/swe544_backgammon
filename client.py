import sys, getopt
import socket

def connectToServer(serverIP, username):
        s = socket.socket()
        #host = socket.gethostname()
        host = serverIP
        port = 10001
        try:
                s.connect((host, port))
        except socket.error as msg:
                print(msg)
                s.close()
                return
        print s.recv(1024)
        paramList = []
        paramList.append(username)
        msg = createMsg("CLOGIN", paramList)
        print(msg)
        #s.send(msg)
        paramList = []
        paramList.append("play")
        msg = createMsg("CREQST", paramList)
        print(msg)
        msg = createMsg("CTDICE", paramList)
        print(msg)
        s.close()

class Client(object):
        """
        Representation of a simple backgammon client
        """
        def __init__(self, serverIP, username):
                """
                Initialize client instance
                serverIP: IP address of the server
                username: username of the client
                boardState: Show the current status of the board
                state: Shows the current state of the client
                All the states:
                        IDLE       -> CONNECTING
                        CONNECTING -> IDLE | CONNECTED
                        CONNECTED  -> WATCH_REQ | PLAY_REQ
                        WATCH_REQ  -> WATCHING
                        PLAY_REQ   -> PLAYING
                        LEAVE_REQ  -> LEFT
                """
                self.serverIP = serverIP
                self.port = 10001
                self.username = username
                self.boardState = {} # may be changed later to sth else
                self.state = 'IDLE'
                self.allowedMessages = {}
                self.allowedUserCmds = {}
                #self.allowedUserCmds["play"] = 0
                #self.allowedUserCmds["watch"] = 0
                #self.allowedUserCmds["leave"] = 0

        def createEmptyMsg(self, msgType):
                """
                Creates a msg whose body is empty
                msgType: CTDICE, CLPONG, CLRJCTM
                """
                msg = str(msgType)
                msg = msg + "\n\r\n{\n}"
                #print(msg)
                return msg

        def createFilledMsg(self, msgType, paramList):
                """
                Creates a msg whose body is not empty. Not directly called, instead
                called by relevant wrappers
                msgType: CLOGIN, CREQST, CRJCTM
                paramList depends on the msgType, filled by the specific msg handler
                """
                msg = str(msgType)
                msg = msg + "\n\r\n{\n\t\""
                msg = msg + str(paramList[0]) + "\": \"" + str(paramList[1]) + "\",\n}"
                #print(msg)
                return msg

        def createLoginMsg(self, username):
                """
                Prepares a login msg to be sent to the server
                userid: username
                """
                paramList = []
                paramList.append("userid")
                paramList.append(username)
                return self.createFilledMsg("CLOGIN", paramList)

        def createRequestMsg(self, request):
                """
                Prepares a request msg to be sent to the server
                request: play or watch or leave
                """
                paramList = []
                paramList.append("type")
                paramList.append(request)
                return self.createFilledMsg("CREQST", paramList)

        def createMoveMsg(self, move):
                """
                Prepares a move msg to be sent to the server
                move: move in backgammon notation
                """
                paramList = []
                paramList.append("move")
                paramList.append(move)
                return self.createFilledMsg("CMOVEC", paramList)

        def run(self):
                """
                TODO: purpose of the method
                """
                print('serverIP is ' + self.serverIP)
                print('username is ' + self.username)
                # Connection to the server failed
                if self.sessionSetup() is False:
                        return;

                # TODO: print message here
                print("Hi " + self.username)

                # introduce a main loop here. If necessary move it to another method
                while True:
                        self.s.recv(1024)
                #paramList = []
                #paramList.append(username)
                #msg = createMsg("CLOGIN", paramList)
                #print(msg)
                ##s.send(msg)
                #paramList = []
                #paramList.append("play")
                #msg = createMsg("CREQST", paramList)
                #print(msg)
                #msg = createMsg("CTDICE", paramList)
                #print(msg)
                #s.close()

        def sendLoginRequest(self):
                """
                Prepares and sends a login message to the server
                """
                msg = self.createLoginMsg(self.username)
                #print(msg)
                self.s.send(msg)

        def handleLoginResponse(self):
                """
                Handles login response sent by the server
                """
                message = self.s.recv(1024)
                print(message)

                msg = message
                msgList = msg.split('\n')
                if msgList[0] != 'SLRSPS':
                        return False
                msgList = msgList[3].split(':')
                key = msgList[0].split('"')[1]
                if key != 'result':
                        return False
                val = msgList[1].split('"')[1]
                #print(val)

                if val == "fail":
                        return False
                return True

        def sessionSetup(self):
                """
                Makes a connection to the server and then attempts to log in
                """
                # Open a socket
                self.s = socket.socket()
                try:
                        self.s.connect((self.serverIP, self.port))
                except socket.error as msg:
                        print(msg)
                        self.s.close()
                        return False

                self.state = "CONNECTING"
                # Send a login request to the server
                self.sendLoginRequest()

                # Handle the response returned by the server. Might be success or failure
                if self.handleLoginResponse() is False:
                        self.s.close()
                        self.state = "IDLE"
                        return False
                self.state = "CONNECTED"
                return True

        def handleHeartbeat(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleUserInput(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def updateBoardState(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def showBoardState(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def __str__(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendWatchRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleWatchResponse(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleWatchState(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendLeaveRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendPlayRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handlePlayResponse(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleWaitingState(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handlePlayingState(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

def usage():
        print('client.py -s <serverIP> -u <username>')
        sys.exit(-1)

def parseArgs(argv):
        serverIP = ''
        username = ''

        if sys.argv[1:] == []:
                usage()

        try:
                opts, args = getopt.getopt(argv, "s:u:")
        except getopt.GetoptError:
                usage()
        for opt, arg in opts:
                if opt == '-s':
                        serverIP = arg
                elif opt == '-u':
                        username = arg
                else:
                        usage()
        #connectToServer(serverIP, username)
        #print('serverIP is ' + serverIP)
        #print('username is ' + username)
        return serverIP, username

if __name__ == "__main__":
        serverIP, username = parseArgs(sys.argv[1:])
        c = Client(serverIP, username)
        c.run()

