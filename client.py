import sys, getopt
import socket

def createMsg(msgType, paramList):
        msg = str(msgType)
        msg = msg + "\n\r\n{\n"

        if msgType == "CTDICE":
                msg = msg + "}"
                return msg
        elif msgType == "CLOGIN":
                key = "userid"
        elif msgType == "CREQST":
                key = "type"
        elif msgType == "CMOVEC":
                key = "move"

        msg = msg + "\t\"" + key + "\": \"" + str(paramList[0]) + "\"\n}"
        #msg = msg + "\t\"type\": \"" + str(paramList[0]) + "\"\n}"
        #if msgType == "CLOGIN":
                #msg = msg + "\t\"userid\": \"" + str(paramList[0]) + "\"\n}"
        #elif msgType == "CREQST":
                #msg = msg + "\t\"type\": \"" + str(paramList[0]) + "\"\n}"
        #elif msgType == "CMOVEC":
                #msg = "\t\"move\": \"" + str(paramList[0]) + "\"\n}"

        #print(msg)
        return msg

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

def usage():
        print('client.py -s <serverIP> -u <username>')
        sys.exit(-1)

def main(argv):
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
        print('serverIP is ' + serverIP)
        print('username is ' + username)
        connectToServer(serverIP, username)

if __name__ == "__main__":
        main(sys.argv[1:])

