
def createEmptyMsg(msgType):
        """
        Creates a msg whose body is empty
        """
        msg = str(msgType)
        msg = msg + "\n\r\n{\n}"
        #print(msg)
        return msg

def createFilledMsg(msgType, paramList):
        """
        Creates a msg whose body is not empty.
        paramList depends on the msgType, filled by the specific msg handler
        TODO: it should handle more than one key=value pair
        """
        msg = str(msgType)
        msg = msg + "\n\r\n{\n\t\""
        msg = msg + str(paramList[0]) + "\": \"" + str(paramList[1]) + "\",\n}"
        #print(msg)
        return msg

def getMsgHeader(msg):
        """
        TODO: purpose of the method
        """
        raise NotImplementedError

def getMsgBody(msg):
        """
        TODO: purpose of the method
        Return as a list i.e. ['key', 'value', 'key', 'value', ...]
        """
        raise NotImplementedError

def parseMsg(msg):
        """
        TODO: purpose of the method
        Should return msgType and its key=value pair(s) if exists
        """
        raise NotImplementedError

def createHeartbeatMsg():
        """
        Prepares a ping msg to be sent to the client
        """
        return createEmptyMsg("SVPING")

def createLoginMsg(username):
        """
        Prepares a login msg to be sent to the server
        userid: username
        """
        paramList = []
        paramList.append("userid")
        paramList.append(username)
        #return createFilledMsg("CLOGIN", paramList)
        return createFilledMsg("CLOGIN", paramList)

def createRequestMsg(request):
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramList = []
        paramList.append("type")
        paramList.append(request)
        #return createFilledMsg("CREQST", paramList)
        return createFilledMsg("CREQST", paramList)

def createMoveMsg(move):
        """
        Prepares a move msg to be sent to the server
        move: move in backgammon notation
        """
        paramList = []
        paramList.append("move")
        paramList.append(move)
        #return createFilledMsg("CMOVEC", paramList)
        return createFilledMsg("CMOVEC", paramList)

def createLoginResponseMsg(result):
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramList = []
        paramList.append("result")
        paramList.append(result)
        return createFilledMsg("SLRSPS", paramList)

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


