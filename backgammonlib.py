
def isEmpty(anyStructure):
        """
        Checks if any structure (dict, list, tuple, ... etc) is empty or not
        """
        if anyStructure:
                return False
        else:
                return True

def createMsgWithEmptyBody(msgType):
        """
        Creates a msg whose body is empty

        msgType: msg header
        """
        msg = str(msgType)
        msg = msg + "\n\r\n{\n}"
        #print(msg)
        return msg

def createMsgWithFilledBody(msgType, paramDict):
        """
        Creates a msg whose body is filled (not empty)

        msgType: msg header
        paramDict depends on the msgType, filled by the specific msg handler
        """
        #print('createMsgWithFilledBody')
        msg = str(msgType)
        #msg = msg + "\n\r\n{\n\t\""
        msg = msg + "\n\r\n{"
        for key in paramDict:
                msg = msg + '\n\t\"' + str(key) + '\": \"' + str(paramDict[key]) + '\",'
        msg = msg + '\n}'
        #print(msg)
        return msg

def getMsgHeader(msg):
        """
        Gets and returns message header
        """
        #print('getMsgHeader: ', msg.split('\n'))
        return msg.split('\n')[0]

def getMsgBody(message):
        """
        Gets and returns message body as a dict {key1:val1, key2:val2, ...}
        """
        #print('getMsgBody')
        msg = message.split('\n')
        #print(msg)
        paramDict = {}
        for i in range(3, len(msg) -1):
                #print('msg[i]: ', msg[i])
                e = msg[i][1:len(msg[i])-1].split(': ')
                #print('e: ', e)
                #print(e[0], e[1])
                key = str(e[0][1:len(e[0])-1])
                try:
                        value = str(e[1][1:len(e[1])-1])
                except IndexError:
                        print('BUG: getMsgBody')
                        print(message)
                        print(msg)
                        print('e: ', e)
                        print('key: ' + key)
                paramDict[key] = value

        #print(paramDict)
        return paramDict

def createServerRejectMsg(boardstate):
        """
        Creates a server reject msg

        boardstate: should be the latest valid boardstate, which is hold
        by the server authoritatively
        """
        paramDict = {}
        paramDict["boardstate"] = boardstate
        return createMsgWithFilledBody("SRJCTM", paramDict)

def createClientRejectMsg():
        """
        Creates a client reject msg
        """
        return createMsgWithEmptyBody("CRJCTM")

def createServerMoveMsg(move):
        """
        Creates a server move msg

        move: in backgammon notation
        """
        paramDict = {}
        paramDict["move"] = move
        return createMsgWithFilledBody("SMOVEC", paramDict)

def createClientMoveMsg(move):
        """
        Creates a client move msg

        move: in backgammon notation
        """
        paramDict = {}
        paramDict["move"] = move
        return createMsgWithFilledBody("CMOVEC", paramDict)

def createServerThrowDiceMsg(dice1, dice2):
        """
        Creates a server dice msg

        dice1: first dice value between [1,6]
        dice2: second dice value between [1,6]
        """
        paramDict = {}
        paramDict['dice1'] = str(dice1)
        paramDict['dice2'] = str(dice2)
        return createMsgWithFilledBody("STDICE", paramDict)

def createClientThrowDiceMsg():
        """
        Creates a client dice msg
        """
        return createMsgWithEmptyBody("CTDICE")

def createTeardownMsg():
        """
        Creates a server teardown msg
        """
        return createMsgWithEmptyBody("STEARD")

def createSvrnokMsg():
        """
        Creates a server svrnok msg
        """
        return createMsgWithEmptyBody("SVRNOK")

def createPingMsgDebug(msgId):
        """
        Creates a ping msg with an id to be sent to the client

        msgId: a number between [1-99999]
        """
        paramDict = {}
        paramDict['msgId'] = str(msgId)
        return createMsgWithFilledBody("SVPING", paramDict)

def createPongMsgDebug(msgId):
        """
        Creates a pong msg with an id of SVPING to be sent to the server

        msgId: a number between [1-99999]
        """
        paramDict = {}
        paramDict['msgId'] = str(msgId)
        return createMsgWithFilledBody("CLPONG", paramDict)

def createPingMsg():
        """
        Creates a ping msg to be sent to the client
        """
        return createMsgWithEmptyBody("SVPING")

def createPongMsg():
        """
        Creates a pong msg to be sent to the server
        """
        return createMsgWithEmptyBody("CLPONG")

def createSuccessResponseToLoginRequest():
        """
        Creates server successful login response msg
        """
        paramDict = {}
        paramDict["result"] = 'success'
        return createMsgWithFilledBody("SLRSPS", paramDict)

def createFailResponseToLoginRequest():
        """
        Creates server failure login response msg
        """
        paramDict = {}
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createLoginRequestMsg(username):
        """
        Creates client login msg

        userid: username of the client
        """
        paramDict = {}
        paramDict["userid"] = username
        return createMsgWithFilledBody("CLOGIN", paramDict)

def createSuccessResponseToPlayRequest(username, color, turn):
        """
        Creates server response to a successful play request sent by client

        username: opponent's username
        color: color of the user
        turn: whose turn to begin playing
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
        Creates server response to a failing play request sent by client
        """
        paramDict = {}
        paramDict["type"] = 'play'
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createSuccessResponseToWatchRequest(gObject):
        """
        Creates server response to a successful watch request sent by the client

        gObject refers to a Game object/instance
        """
        paramDict = {}
        paramDict["type"] = 'watch'
        paramDict["result"] = 'success'
        paramDict["player1"] = gObject.getp1Username()
        paramDict["player2"] = gObject.getp2Username()
        paramDict["player1_color"] = gObject.getp1Color()
        paramDict["player2_color"] = gObject.getp2Color()
        paramDict["score"] = gObject.getScore()
        paramDict["player_turn"] = gObject.getTurn()
        paramDict["boardstate"] = gObject.getBoard()
        return createMsgWithFilledBody("SREQRP", paramDict)

def createFailResponseToWatchRequest():
        """
        Creates server response to a failing watch request sent by client
        """
        paramDict = {}
        paramDict["type"] = 'watch'
        paramDict["result"] = 'fail'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createSuccessResponseToLeaveRequest():
        """
        Creates server response to a successful leave request sent by the client
        """
        paramDict = {}
        paramDict["type"] = 'leave'
        paramDict["result"] = 'success'
        return createMsgWithFilledBody("SREQRP", paramDict)

def createPlayRequest():
        """
        Creates client play request
        """
        paramDict = {}
        paramDict["type"] = 'play'
        return createMsgWithFilledBody("CREQST", paramDict)

def createWatchRequest():
        """
        Creates client watch request
        """
        paramDict = {}
        paramDict["type"] = 'watch'
        return createMsgWithFilledBody("CREQST", paramDict)

def createLeaveRequest():
        """
        Creates client leave request
        """
        paramDict = {}
        paramDict["type"] = 'leave'
        return createMsgWithFilledBody("CREQST", paramDict)

class BackgammonBoard(object):
        """
        Representation of a backgammon board
        """

        def __init__(self):
                """
                Default constructor.

                Called when a new game or set begins by the server
                It may also be used by a Player or a Watcher
                """
                print('BackgammonBoard default constructor')
                self.board = {} # may be changed later to sth else

        def __init__(self, boardState):
                """
                Copy Constructor. Called by a watcher when the watch request
                of a client is accepted by the server so that watcher can make
                its copy of boardState the same as of the server
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


