import socket
from threading import Timer

userList = {}
heartbeat = 10.0
clientSocketList = []

def createFilledMsg(msgType, paramList):
        """
        """
        msg = str(msgType)
        msg = msg + "\n\r\n{\n\t\""
        msg = msg + str(paramList[0]) + "\": \"" + str(paramList[1]) + "\",\n}"
        print(msg)
        return msg

def createLoginResponseMsg(result):
        """
        Prepares a request msg to be sent to the server
        request: play or watch or leave
        """
        paramList = []
        paramList.append("result")
        paramList.append(result)
        return createFilledMsg("SLRSPS", paramList)

def checkUsername(username):
        """
        """
        return True

def handleLoginRequest(message):
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
        if userList.get(username) is None and checkUsername(username):
                userEntry.append(username)
                userList[username] = 'CONNECTED'
                return True, username
        return False, username

def sendLoginResponse(result):
        if result is False:
                msg = createLoginResponseMsg("fail")
        else:
                msg = createLoginResponseMsg("success")
        return msg

def sendHeartbeatMsg():
        print("heartbeat")
        #t = Timer(heartbeat, sendHeartbeatMsg)
        #t.start()

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
port = 10001
print('My IP address: ' + host)
s.bind((host, port))
s.listen(5)

#t = Timer(heartbeat, sendHeartbeatMsg)
#t.start()

while True:
        c, addr = s.accept()
        print('Got connection from', addr)
        #c.send('Thank you for connection!')
        msg = c.recv(1024)
        print(msg)
        #print(handleLoginRequest(msg))
        result, username = handleLoginRequest(msg)
        if result is False:
                print('FAIL: ' + str(username) + ' already exists. Choose another username')
        else:
                print('OK: ' + str(username) + '. You are logged in to the server')
        c.send(sendLoginResponse(result))
        #c.close()


