import sys, getopt
import socket
from backgammonlib import *
import select

def connectToServer(serverIP, username):
        s = socket.socket()
        #host = socket.gethostname()
        host = serverIP
        port = 10001
        try:
                s.connect((host, port))
        except socket.error as err:
                print(err)
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
                self.state = 'IDLE'
                self.allowedMessages = {}
                self.allowedUserCmds = {}
                self.initUserCmds()
                self.poller = -1
                self.fdToObject = {}
                self.userType = 'unknown'

        def initUserCmds(self):
                """
                TODO: purpose of the method
                """
                self.allowedUserCmds['play']= 'off'
                self.allowedUserCmds['watch']= 'off'
                self.allowedUserCmds['leave']= 'off'
                self.allowedUserCmds['dice']= 'off'
                self.allowedUserCmds['move']= 'off'
                self.allowedUserCmds['reject']= 'off'

        def sendLoginRequest(self):
                """
                Prepares and sends a login message to the server
                """
                msg = createLoginRequestMsg(self.username)
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

                self.allowedUserCmds['play'] = 'on'
                self.allowedUserCmds['watch'] = 'on'
                self.state = "CONNECTED"
                return True

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
                                                msg = self.s.recv(1024)
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

        def handleUserInputConnectedState(self, userInput):
                """
                TODO: purpose of the method
                """
                sMsg = False
                try:
                        if 1 == int(userInput):
                                sMsg = createPlayRequest()
                                self.disableInput()
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

        def handleUserInput(self, userInput):
                """
                Handles user input

                Will be calling
                        handleConnectedState if state is CONNECTED
                        handlePlayingState if state is PLAYING
                        handleWatchingState if state is WATCHING
                        handleLeavingState if state is LEAVING
                """
                if self.state is 'CONNECTED':
                        self.handleUserInputConnectedState(userInput)

        def handleServerInput(self, rMsg):
                """
                Handles the messages sent by the server

                Will be calling
                        handleRequestResponse (SREQRP) if state is CONNECTED
                        handleServerThrownDice (STDICE) if state is PLAYING or state is WATCHING
                        handleServerRejectMove (SRJCTM) if state is PLAYING or state is WATCHING
                        handleServerNOK if state is not IDLE
                        handleHeartbeat (SVPONG) if state is not IDLE
                        handleMove (SMOVEC) if state is PLAYING or state is WATCHING
                """
                #print(rMsg)
                header = getMsgHeader(rMsg)
                #print('header: ' + header)
                sMsg = False
                if rMsg == '':
                        return False
                elif header == 'SVPING':
                        #print('creating pong rMsg')
                        sMsg = createPongMsg()
                        if sMsg is not False:
                                self.s.send(sMsg)
                elif header == 'SREQRP':
                        self.handleRequestResponse(rMsg)
                elif header == 'SVRNOK':
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
                print('handleRequestResponse')
                print(rMsg)
                paramDict = getMsgBody(rMsg)
                request = paramDict['type']
                if request == 'play' and self.state == 'PLAY_REQ':
                        result = paramDict['result']
                        if result == 'fail':
                                print('result is fail')
                                self.state = 'WAITING'
                                self.enableInput()
                                self.failedPlayScreen()
                        elif result is 'success':
                                print('NE MUTLU TURKUM DIYENE')

        def handleConnectedState(self):
                """
                TODO: purpose of the method

                Will be calling
                        sendPlayRequest (CREQST) if state is CONNECTED and allowedUserCmds['play'] is 'on'
                        sendWatchRequest (CREQST) if state is CONNECTED and allowedUserCmds['watch'] is 'on'
                """
                raise NotImplementedError

        def handlePlayingState(self):
                """
                TODO: purpose of the method

                Will be calling
                        sendThrowDice (CTDICE) if state is PLAYING and turn == 1 and allowedUserCmds['dice'] is 'on'
                        sendMove (CMOVEC) if state is PLAYING and turn == 1 and allowedUserCmds['move'] is 'on'
                """
                raise NotImplementedError

        def handleWaitingState(self):
                """
                TODO: purpose of the method
                Will be calling
                        sendLeaveRequest if state is WAITING
                """
                raise NotImplementedError

        def handleWatchingState(self):
                """
                TODO: purpose of the method
                Will be calling
                        sendLeaveRequest if state is WATCHING (CREQST)
                """
                raise NotImplementedError

        def handlePlayResponse(self):
                """
                TODO: purpose of the method
                state is either 'PLAYING' or 'WAITING'
                state is PLAYING.
                        learn whose turn is
                        if turn is ours:
                                allowedUserCmds['dice'] = 'on'
                                allowedUserCmds['others'] = 'off'
                        else:
                                allowedUserCmds['all'] = 'off'

                state is WAITING.
                        allowedUserCmds['leave'] = 'on'
                        allowedUserCmds['others'] = 'off'
                """
                raise NotImplementedError

        def handleWatchResponse(self):
                """
                TODO: purpose of the method
                state is either 'WATCHING' or 'CONNECTED'
                state is WATCHING.
                        allowedUserCmds['leave'] = 'on'
                        allowedUserCmds['others'] = 'off'
                state is CONNECTED.
                        allowedUserCmds['play'] = 'on'
                        allowedUserCmds['watch'] = 'on'
                        allowedUserCmds['others'] = 'off'
                """
                raise NotImplementedError

        def handleLeaveResponse(self):
                """
                TODO: purpose of the method
                state is LEAVING
                        allowedUserCmds['all'] = 'off'
                """
                raise NotImplementedError

        def handleServerThrownDice(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleServerRejectMove(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleServerNOK(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def handleHeartbeat(self):
                """
                TODO: purpose of the method
                call sendHeartbeatMsg -> CLPONG
                """
                raise NotImplementedError

        def handleMove(self):
                """
                TODO: purpose of the method
                call sendThrowDice -> CTDICE or sendReject -> CRJCTM
                """
                raise NotImplementedError

        def sendPlayRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendWatchRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendLeaveRequest(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendThrowDice(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def sendMove(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

        def __str__(self):
                """
                TODO: purpose of the method
                """
                raise NotImplementedError

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

