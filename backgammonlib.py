
def createMsgWithEmptyBody(msgType):
        """
        Creates a msg whose body is empty
        """
        msg = str(msgType)
        msg = msg + "\n\r\n{\n}"
        #print(msg)
        return msg

def createMsgWithFilledBody(msgType, paramDict):
        """
        Creates a msg whose body is not empty.
        paramDict depends on the msgType, filled by the specific msg handler
        TODO: it should handle more than one key=value pair
        """
        #print('createMsgWithFilledBody')
        msg = str(msgType)
        #msg = msg + "\n\r\n{\n\t\""
        msg = msg + "\n\r\n{"
        #msg = msg + str(paramList[0]) + "\": \"" + str(paramList[1]) + "\",\n}"
        for key in paramDict:
                msg = msg + '\n\t\"' + str(key) + '\": \"' + str(paramDict[key]) + '\",'
        msg = msg + '\n}'
        #print(msg)
        return msg

def getMsgHeader(msg):
        """
        TODO: purpose of the method
        """
        #print('getMsgHeader: ', msg.split('\n'))
        return msg.split('\n')[0]

def getMsgBody(message):
        """
        TODO: purpose of the method
        Return as a list i.e. ['key', 'value', 'key', 'value', ...]
        """
        #print('getMsgBody')
        msg = message.split('\n')
        #print(msg)
        paramDict = {}
        for i in range(3, len(msg) -1):
                #print('msg[i]: ', msg[i])
                e = msg[i][1:len(msg[i])-1].split(': ')
                #print('e: ', e)
                #print(entry[0], entry[1])
                key = str(e[0][1:len(e[0])-1])
                value = str(e[1][1:len(e[1])-1])
                paramDict[key] = value

        #print(paramDict)
        return paramDict

def createSvrnokMsg():
        """
        Prepares a svrnok (SVRNOK) msg to be sent to the client
        """
        return createMsgWithEmptyBody("SVRNOK")

def createPingMsg():
        """
        Prepares a ping (SVPING) msg to be sent to the client
        """
        return createMsgWithEmptyBody("SVPING")

def createPongMsg():
        """
        Prepares a pong (CLPONG) msg to be sent to the server
        """
        return createMsgWithEmptyBody("CLPONG")

def createSuccessResponseToLoginRequest():
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["result"] = 'success'
        return createMsgWithFilledBody("SLRSPS", paramDict)

def createFailResponseToLoginRequest():
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createLoginRequestMsg(username):
        """
        Prepares a login (CLOGIN) msg to be sent to the server
        userid: username
        """
        paramDict = {}
        paramDict["userid"] = username
        return createMsgWithFilledBody("CLOGIN", paramDict)

def createSuccessResponseToPlayRequest(username, color, turn):
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["type"] = 'play'
        paramDict["result"] = 'success'
        paramDict["opponent"] = username
        paramDict["color"] = color
        paramDict["turn"] = turn
        return createMsgWithFilledBody("SREQRP", paramDict)

def createFailResponseToPlayRequest():
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["type"] = 'play'
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createFailResponseToWatchRequest():
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["type"] = 'watch'
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createSuccessResponseToLeaveRequest():
        """
        TODO: purpose of the method
        """
        paramDict = {}
        paramDict["type"] = 'leave'
        paramDict["result"] = 'success'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createPlayRequest():
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramDict = {}
        paramDict["type"] = 'play'
        #paramList = []
        #paramList.append("type")
        #paramList.append('play')
        #return createMsgWithFilledBody("CREQST", paramList)
        return createMsgWithFilledBody("CREQST", paramDict)

def createWatchRequest():
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramDict = {}
        paramDict["type"] = 'watch'
        #paramList = []
        #paramList.append("type")
        #paramList.append('watch')
        #return createMsgWithFilledBody("CREQST", paramList)
        return createMsgWithFilledBody("CREQST", paramDict)

def createLeaveRequest():
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramDict = {}
        paramDict["type"] = 'leave'
        #paramList = []
        #paramList.append("type")
        #paramList.append('leave')
        #return createMsgWithFilledBody("CREQST", paramList)
        return createMsgWithFilledBody("CREQST", paramDict)

def createMoveMsg(move):
        """
        Prepares a move msg to be sent to the server
        move: move in backgammon notation
        """
        paramDict = {}
        paramDict["move"] = move
        #paramList = []
        #paramList.append("move")
        #paramList.append(move)
        #return createMsgWithFilledBody("CMOVEC", paramList)
        return createMsgWithFilledBody("CMOVEC", paramDict)

class BackgammonBoard(object):
        """
        Representation of a backgammon board
        """

        def __init__(self):
                """
                Default constructor. Called when a new game or set begins
                """
                print('BackgammonBoard default constructor')
                self.board = {} # may be changed later to sth else

        def __init__(self, boardState):
                """
                Copy Constructor. Called when watch request is accepted by the server
                """
                print('BackgammonBoard copy constructor')
                self.board = boardState

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


