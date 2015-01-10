import sys, getopt
import socket
from backgammonlib import *
import select

rMsgSize = 1024

class Client(object):
        """
        Representation of a simple backgammon client
        send -requests-
                CLOGIN, CREQST,
                CTDICE (at the beginning of a new set or game),
                CMOVEC
        receive -responses-
                SLRSPS (CLOGIN), SREQRP(CREQST),
                STDICE(CTDICE), SRJCTM(CMOVEC), STDICE(CMOVEC)
                SVRNOK (CLOGIN, CREQST, CTDICE, CMOVEC)

        receive -requests-
                SVPING, SMOVEC
        send -responses-
                CLPONG (SVPING)
                CTDICE (SMOVEC), CRJCTM(SMOVEC)

        receive -messages-
                SSTOVR, SGMOVR, STEARD

        created messages:empty body  : CTDICE, CLPONG, CLRJCTM
        created messages:filled body : CLOGIN, CREQST, CMOVEC
        received messages:empty body : SVRNOK, SVPING, STEARD
        received messages:filled body: SLRSPS, SREQRP, STDICE, SRJCTM, SMOVEC, SSTOVR, SGMOVR
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
                self.s = -1
                self.state = 'IDLE'
                self.poller = -1
                self.fdToObject = {}
                self.userType = 'unknown'
                self.p = -1 # Player object
                self.w = -1 # Watcher object

        def sendLoginRequest(self):
                """
                Prepares and sends a login message to the server
                """
                msg = createLoginRequestMsg(self.username)
                #print(msg)
                self.s.send(msg)

        #def handleLoginResponse(self):
                #"""
                #Handles login response sent by the server
                #"""
                #message = self.s.recv(rMsgSize)
                #print(message)

                #msg = message
                #msgList = msg.split('\n')
                #if msgList[0] != 'SLRSPS':
                        #return False
                #msgList = msgList[3].split(':')
                #key = msgList[0].split('"')[1]
                #if key != 'result':
                        #return False
                #val = msgList[1].split('"')[1]
                ##print(val)

                #if val == "fail":
                        #return False
                #return True

        def handleLoginResponse(self):
                """
                Handles login response sent by the server
                """
                rMsg = self.s.recv(rMsgSize)
                #print(rMsg)

                header = getMsgHeader(rMsg)
                if header != 'SLRSPS':
                        return False
                paramDict = getMsgBody(rMsg)
                result = paramDict['result']
                if result == 'fail':
                        return False
                elif result == 'success':
                        return True
                return False

        def sessionSetup(self):
                """
                Makes a connection to the server and then attempts to log in
                """
                # Open a socket
                self.s = socket.socket()
                try:
                        self.s.connect((self.serverIP, self.port))
                except socket.error as err:
                        print(err)
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

        def run(self):
                """
                Main loop of a client
                """
                print('serverIP is ' + self.serverIP)
                print('username is ' + self.username)
                # Connection to the server failed
                if self.sessionSetup() is False:
                        print('connection is refused by the server')
                        return

                # print welcome message
                print("Hi " + self.username)
                self.connectedScreen()

                READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
                self.poller = select.poll()
                self.fdToObject[self.s.fileno()] = self.s
                self.fdToObject[sys.stdin.fileno()] = sys.stdin
                self.poller.register(self.s, READ_ONLY)
                self.poller.register(sys.stdin, READ_ONLY)
                out = False
                while True:
                        events = self.poller.poll()
                        for fd, flag in events:
                                o = self.fdToObject[fd]
                                if flag & (select.POLLIN | select.POLLPRI):
                                        if o is self.s:
                                                msg = self.s.recv(rMsgSize)
                                                if self.handleServerInput(msg) is False:
                                                        out = True
                                                        break
                                        if o is sys.stdin:
                                                userInput = sys.stdin.readline()
                                                self.handleUserInput(userInput)
                        if out is True:
                                break

                self.poller.unregister(self.s)
                self.s.close()

        def disableInput(self):
                """
                TODO: purpose of the method
                """
                self.poller.unregister(sys.stdin)

        def enableInput(self):
                """
                TODO: purpose of the method
                """
                self.poller.register(sys.stdin)

        def connectedScreen(self):
                """
                TODO: purpose of the method
                """
                print("(1) Play")
                print("(2) Watch")
                sys.stdout.write("> ")
                sys.stdout.flush()

        def failedPlayScreen(self):
                """
                TODO: purpose of the method
                """
                print("No opponent to play")
                print("Waiting an opponent...")
                print("(3) Leave")
                sys.stdout.write("> ")
                sys.stdout.flush()

        def failedWatchScreen(self):
                """
                TODO: purpose of the method
                """
                print("No game to watch")
                self.connectedScreen()

        def failedLeavingScreen(self):
                """
                TODO: purpose of the method
                """
                print("(3) Leave")
                sys.stdout.write("> ")
                sys.stdout.flush()

        def handleUserInput(self, userInput):
                """
                TODO: purpose of the method
                """
                #print('handleUserInput')
                #print('===============')
                #print('self.state is ' + self.state)
                sMsg = False
                if self.state is 'CONNECTED':
                        try:
                                if 1 == int(userInput):
                                        self.disableInput()
                                        sMsg = createPlayRequest()
                                        self.state = 'PLAY_REQ'
                                elif 2 == int(userInput):
                                        self.disableInput()
                                        sMsg = createWatchRequest()
                                        self.state = 'WATCH_REQ'
                                else:
                                        self.connectedScreen()
                        except ValueError:
                                self.connectedScreen()
                        if sMsg is not False:
                                self.s.send(sMsg)
                elif self.state is 'WAITING':
                        try:
                                if 3 == int(userInput):
                                        self.disableInput()
                                        sMsg = createLeaveRequest()
                                else:
                                        self.failedLeavingScreen()
                        except ValueError:
                                self.failedLeavingScreen()
                        if sMsg is not False:
                                self.s.send(sMsg)
                                self.state = 'LEAVING'
                elif self.state is 'PLAYING':
                        self.p.handleUserInput(userInput)
                elif self.state is 'WATCHING':
                        self.w.handleUserInput(userInput)
                else:
                        print('user input in a state(' + self.state + ') which is not valid')

        def handleServerInput(self, rMsg):
                """
                TODO: purpose of the method
                """
                #print('handleServerInput')
                #print('=================')
                #print('self.state is ' + self.state)
                #print(rMsg)
                header = getMsgHeader(rMsg)
                #print('header: ' + header)
                sMsg = False
                if rMsg == '': # server closed the socket
                        return False
                elif header == 'SREQRP' and self.state is 'LEAVING':
                        return False
                elif header == 'SVPING':
                        #print('creating pong rMsg')
                        #print('SVPING - '),
                        paramDict = getMsgBody(rMsg)
                        #print(paramDict["msgId"]),
                        sMsg = createPongMsg(paramDict["msgId"])
                        if sMsg is not False:
                                self.s.send(sMsg)
                                #print(' - CLPONG')
                elif header == 'SREQRP' and (self.state is 'PLAY_REQ' or
                                             self.state is 'WATCH_REQ' or
                                             self.state is 'WAITING'):
                        self.handleRequestResponse(rMsg)
                elif self.state is 'PLAYING':
                        self.p.handleServerInput(rMsg)
                elif self.state is 'WATCHING':
                        self.w.handleServerInput(rMsg)
                elif header == 'SVRNOK' and (self.state is 'PLAY_REQ' or
                                             self.state is 'WATCH_REQ' or
                                             self.state is 'WAITING'):
                        print(rMsg)
                        # TODO: check if they need to be removed or changed
                        self.state = 'CONNECTED'
                        self.enableInput()
                elif header == 'SVRNOK': #TODO: in what situations?
                        print(rMsg)
                        # TODO: check if they need to be removed or changed
                        self.state = 'CONNECTED'
                        self.enableInput()
                else:
                        print('unknown message from the server')
                        print(rMsg)
                return True

        def handleRequestResponse(self, rMsg):
                """
                TODO: purpose of the method
                """
                #print('handleRequestResponse')
                #print('=====================')
                #print(rMsg)
                paramDict = getMsgBody(rMsg)
                request = paramDict['type']
                result = paramDict['result']
                if request == 'play' and self.state == 'PLAY_REQ':
                        if result == 'fail':
                                #print('result is fail')
                                self.enableInput()
                                self.state = 'WAITING'
                                self.failedPlayScreen()
                        elif result == 'success':
                                self.state = 'PLAYING'
                                self.p = Player(self.serverIP, self.username, self, rMsg)
                elif request == 'watch' and self.state == 'WATCH_REQ':
                        if result == 'fail':
                                #print('result is fail')
                                self.enableInput()
                                self.state = 'CONNECTED'
                                self.failedWatchScreen()
                        elif result == 'success':
                                self.state = 'WATCHING'
                                self.w = Watcher(self.serverIP, self.username, self, rMsg)
                elif self.state is 'WAITING':
                                self.disableInput()
                                self.state = 'PLAYING'
                                self.p = Player(self.serverIP, self.username, self, rMsg)

        def getSocket(self):
                """
                TODO: purpose of the method
                """
                return self.s

        def __str__(self):
                """
                TODO: purpose of the method
                """
                return self.username

class Player(Client):
        """
        TODO: purpose of the class
        """
        def __init__(self, serverIP, username, client, rMsg):
                """
                TODO: purpose of the method
                """
                Client.__init__(self, serverIP, username)
                print('Player::__init__')
                self.client = client
                self.s = self.client.getSocket()
                self.playingState = 'DICE'
                self.idsToCmd = {}
                self.cmdFlags = {}
                # TODO: create Board Object

                # parse message
                print(rMsg)
                header = getMsgHeader(rMsg)
                if header != 'SREQRP':
                        print('server request response is not SREQRP but ' + header)
                        # TODO: handle it
                paramDict = getMsgBody(rMsg)
                self.color = paramDict["color"]
                self.turn = paramDict["turn"]
                self.opponent = paramDict['opponent']

                # init playing cmdline
                self.initCmds()

                # show playing screen
                self.playingScreen()

        def initIdsToCmd(self):
                """
                TODO: purpose of the method
                """
                self.idsToCmd[4] = 'dice'
                self.idsToCmd[5] = 'move'
                self.idsToCmd[6] = 'reject'

        def initCmds(self):
                """
                TODO: purpose of the method
                """
                self.initIdsToCmd()
                if int(self.turn) == 1:
                        self.cmdFlags['dice'] = '(open)'
                else:
                        self.cmdFlags['dice'] = '(closed)'
                self.cmdFlags['move'] = '(closed)'
                self.cmdFlags['reject'] = '(closed)'

        def playingInputScreen(self):
                """
                TODO: purpose of the method
                """
                print("(4) Dice " + self.cmdFlags['dice'])
                print("(5) Move " + self.cmdFlags['move'])
                print("(6) Reject " + self.cmdFlags['reject'])
                sys.stdout.write("> ")
                sys.stdout.flush()

        def playingScreen(self):
                """
                TODO: purpose of the method
                """
                # match info
                print('You are playing with ' + self.opponent)
                if int(self.turn) == 1:
                        print('You turn to play')
                else:
                        print('Not your turn to play')
                # TODO: board info. create Board object
                print('TODO: *****board state*****')
                self.playingInputScreen()
                self.client.enableInput()

        def handleServerInput(self, rMsg):
                """
                TODO: purpose of the method
                """
                print('Player::handleServerInput')
                print(rMsg)
                #header = getMsgHeader(rMsg)
                #if header is 'STDICE' and self.state is 'DICE':

        def handleUserInput(self, userInput):
                """
                TODO: purpose of the method
                """
                print('Player::handleUserInput')
                sMsg = False
                if self.playingState is 'DICE':
                        try:
                                cmd = self.idsToCmd.get(int(userInput), None)
                                if cmd is not None and self.cmdFlags[cmd] == '(open)':
                                        self.client.disableInput()
                                        sMsg = createClientThrowDiceMsg()
                                        self.playingState = 'WAITING_DICE'
                                        self.cmdFlags[cmd] = '(closed)'
                                else:
                                        self.playingInputScreen()
                        except ValueError:
                                self.playingInputScreen()
                        if sMsg is not False:
                                self.s.send(sMsg)

class Watcher(Client):
        """
        TODO: purpose of the class
        """
        def __init__(self, serverIP, username, client, rMsg):
                """
                TODO: purpose of the method
                """
                Client.__init__(self, serverIP, username)
                print('Watcher::__init__')
                self.client = client
                self.s = self.client.getSocket()
                # TODO: create Board Object

                # parse message
                print(rMsg)
                # TODO: parse rMsg and save match info

                # show watching screen
                self.successfulWatchScreen()

        def successfulWatchScreen(self):
                """
                TODO: purpose of the method
                """
                print('TODO: *****match info*****')
                print('TODO: *****board state*****')
                print("(3) Leave")
                sys.stdout.write("> ")
                sys.stdout.flush()
                self.client.enableInput()

        def handleServerInput(self, rMsg):
                """
                TODO: purpose of the method
                """
                print('Watcher::handleServerInput')
                print(rMsg)
                # TODO: parse and print messages sent by the server

        def handleUserInput(self, userInput):
                """
                TODO: purpose of the method
                """
                #print('Watcher::handleUserInput')
                sMsg = False
                c = self.client
                try:
                        if 3 == int(userInput):
                                c.disableInput()
                                sMsg = createLeaveRequest()
                        else:
                                self.failedLeavingScreen()
                except ValueError:
                        self.failedLeavingScreen()
                if sMsg is not False:
                        self.s.send(sMsg)
                        self.state = 'LEAVING'

def usage():
        """
        TODO: purpose of the method
        """
        print('client.py -s <serverIP> -u <username>')
        sys.exit(-1)

def parseArgs(argv):
        """
        TODO: purpose of the method
        """
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

def checkUsername(username):
        """
        Check username according to the requirements.
        A username may consist of English letters (case sensitive), numerals and underscore.
        However, it can't start with anything other than English letters
        """
        return True

if __name__ == "__main__":
        serverIP, username = parseArgs(sys.argv[1:])
        if checkUsername(username) is False:
                print('A username may consist of English letters (case sensitive), numerals and underscore.')
                print("However, it can't start with anything other than English letters.")
                sys.exit(-2)
        c = Client(serverIP, username)
        c.run()

