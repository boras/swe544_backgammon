import socket
import threading
from threading import Timer
from threading import Event
from backgammonlib import *
import os
import time
import Queue
import select
import random

# Global Variables
# userList is the server-wide list of users userList is accessed by different threads
# Therefore, userListLock must be obtained before accessing it
userList = {}
userListLock = threading.Lock()

clientPongWinOpen = False
commServerAddr='./CommServer_uds_socket'
rMsgSize = 1024
rUdsMsgSize = 128

# Classes
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
                        #print('CommServer: ', username)
                        self.queue.put((username, userUdsSock))

class Heartbeat(threading.Thread):
        """
        Representation of a backgammon user
        """

        def __init__(self, queue, heartbeat=10, backtobackMissingCount=2, delayTime=5):
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
                self.msgId = 1

        def sendHeartbeatMsg(self):
                """
                TODO: purpose of the method
                """
                sMsg = createPingMsg(self.msgId)
                userListLock.acquire()
                for user in userList:
                        s = userList[user][0].getUserSock()
                        print('sendHeartbeatMsg to ' + str(userList[user][0])
                              + ': msgId=' + str(self.msgId))
                        try:
                                s.send(sMsg)
                        except socket.error as err:
                                #print(sMsg)
                                #print(err)
                                pass
                        finally:
                                userList[user][0].setHeartbeatSent(True)
                self.msgId += 1
                if self.msgId == 100000:
                        self.msgId = 1
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
                                #print('Heartbeat: ', userInfo)
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
                        # Check heartbeat seconds expired (approximately)
                        if self.remainingTime >= self.heartbeat:
                                global clientPongWinOpen
                                self.remainingTime = 0
                                clientPongWinOpen = True
                                self.sendHeartbeatMsg()
                                self.checkTimer = Timer(self.delayTime, self.checkUsers)
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
                                if userList[userEntry][0].getHeartbeatSent() is False:
                                        continue
                                if user.update_pongMissingCount() == self.backtobackMissingCount:
                                        udsSock.send('dead')
                                print('checkUsers: ' + user.username + ": "
                                      + str(user.getMissingCount()))
                                userList[userEntry][0].setHeartbeatSent(False)
                        except IndexError:
                                # Heartbeat hasn't had a chance to append it to
                                # userList entry yet. Don't check that user
                                pass
                userListLock.release()

class WaitingRoom(object):
        """
        Representation of a waiting Room
        """
        def __init__(self):
                """
                TODO: purpose of the method
                """
                self.waitingRoom = Queue.Queue()
                self.waitersList = {}
                self.waitingRoomLock = threading.Lock()

        def addToWaitingRoom(self, username):
                """
                TODO: purpose of the method
                """
                # Queue is thread safe
                #print('WaitingRoom: ' + username)
                self.waitingRoom.put(username)
                self.waitingRoomLock.acquire()
                self.waitersList[username] = 'valid'
                self.waitingRoomLock.release()

        def markAsInvalid(self, username):
                """
                TODO: purpose of the method
                """
                # Dict is not thread safe
                self.waitingRoomLock.acquire()
                #self.waitersList[username] = 'invalid'
                del self.waitersList[username]
                self.waitingRoomLock.release()

        def markAsValid(self, username):
                """
                TODO: purpose of the method
                """
                # Dict is not thread safe
                self.waitingRoomLock.acquire()
                self.waitersList[username] = 'valid'
                self.waitingRoomLock.release()

        def getOpponent(self, username):
                """
                TODO: purpose of the method
                """
                while True:
                        # Queue is thread safe
                        try:
                                opponent = self.waitingRoom.get(False)
                                #print('opponent name is ' + opponent)
                        except Queue.Empty:
                                #print('WaitingRoom is empty')
                                return False
                        # There is someone in the waitingRoom but it might be 'invalid'
                        self.waitingRoomLock.acquire()
                        # check if it is marked as 'invalid'
                        flag = self.waitersList.get(opponent, None)
                        # there is a valid opponent
                        if flag == 'valid':
                                self.waitingRoomLock.release()
                                return opponent
                        #else:
                                # there is an opponent but 'deleted'
                                # remove it from waitersList
                                #del self.waitersList[opponent]
                        self.waitingRoomLock.release()

class GameList(object):
        """
        Holds all the games currently on-going in the server
        """

        def __init__(self):
                """
                Constructor of GameList Object

                A game entry has two links:
                    (1) game_id: game_object in idToGame
                    (2) game_object: game_id in gameToId

                There may be concurrent access to GameList. GameListLock serializes
                access to GameList.

                TODO: 'gameId's should be managed more efficiently. i.e. It should
                be recycled after some time. It can't increase all the time but for the
                time being, keep it simple
                """
                self.gameToId = {}
                self.idToGame = {}
                self.gameListLock = threading.Lock()
                self.gameId = 1
                self.nofGames = 0

        def addGameToGameList(self, game):
                """
                TODO: purpose of the method
                """
                self.gameListLock.acquire()
                self.idToGame[self.gameId] = game
                self.gameToId[game] = self.gameId
                self.gameId += 1
                self.nofGames += 1
                self.gameListLock.release()

        def findGame(self):
                """
                TODO: purpose of the method
                """
                self.gameListLock.acquire()
                if self.nofGames == 0:
                        # there is no match
                        self.gameListLock.release()
                        return None
                # there is a match
                while True:
                        gameId = random.choice(range(1,self.gameId))
                        game = self.idToGame.get(gameId, None)
                        if game != None:
                                break
                self.gameListLock.release()
                return game

        def removeGameFromGameList(self, game):
                """
                TODO: purpose of the method
                """
                self.gameListLock.acquire()
                gameId = self.gameToId[game]
                del self.gameToId[game]
                del self.idToGame[gameId]
                self.nofGames -= 1
                self.gameListLock.release()

class Game(threading.Thread):
        """
        Representation of a game
        """

        def __init__(self, p1, p2):
                """
                TODO: purpose of the method
                p1 and p2 are User objects
                """
                threading.Thread.__init__(self)
                self.p1 = p1
                self.p2 = p2
                self.p1Color = -1
                self.p2Color = -1
                self.p1Username = p1.getUsername()
                self.p2Username = p2.getUsername()
                self.playerList = {}
                activePlayer = -1
                passivePlayer = -1
                self.poller = -1
                self.fdToSocket = {}
                self.p1Sock = p1.getUserSock()
                self.p1UdsSock = p1.getUserUdsSock()
                self.p2Sock = p2.getUserSock()
                self.p2UdsSock = p2.getUserUdsSock()
                self.sockList = {}
                self.sockListLock = threading.Lock()
                self.score = "0-0"
                self.p1Points = 0
                self.p2Points = 0
                self.gameState = 'DICE'
                self.gameName = self.p1Username + '_vs_' + self.p2Username
                # TODO: it has to point to a Board object
                self.board = 'board'
                #
                #activePlayerSenderList = []
                #passivePlayerSenderList = []
                #watcherList = []
                #matchBroadcastList = []
                #board
                #score
                #move
                #dice
                #moveResult
                #playerList
                #

        def decideTurn(self):
                """
                Decide who will start the game
                """
                while True:
                        p1Dice = random.choice(range(1, 7))
                        p2Dice = random.choice(range(1, 7))
                        if p1Dice != p2Dice:
                                break
                if p1Dice > p2Dice:
                        self.activePlayer = self.p1
                        self.passivePlayer = self.p2
                        self.playerList[self.p1] = 1
                        self.playerList[self.p2] = 0
                elif p1Dice < p2Dice:
                        self.activePlayer = self.p2
                        self.passivePlayer = self.p1
                        self.playerList[self.p1] = 0
                        self.playerList[self.p2] = 1

        def decideColor(self):
                """
                Decide whose color is white or black
                1 is white, 2 is black
                """
                while True:
                        self.p1Color = random.choice(range(1,3))
                        self.p2Color = random.choice(range(1,3))
                        #print(self.p1.getUsername() + ': ' + str(self.p1Color))
                        #print(self.p2.getUsername() + ': ' + str(self.p2Color))
                        if self.p1Color != self.p2Color:
                                break
                #print('out_of_loop: ' + self.p1.getUsername() + ': ' + str(self.p1Color))
                #print('out_of_loop: ' + self.p2.getUsername() + ': ' + str(self.p2Color))
                if self.p1Color == 1:
                        self.p1Color = 'white'
                else:
                        self.p1Color = 'black'
                if self.p2Color == 1:
                        self.p2Color = 'white'
                else:
                        self.p2Color = 'black'

        def sendPlayResponse(self, p, c, t):
                """
                TODO: purpose of the method
                """
                if p == self.p1:
                        u = self.p2Username
                elif p == self.p2:
                        u = self.p1Username
                sMsg = createSuccessResponseToPlayRequest(u, c, t)
                #print(u + ': sending sendPlayResponse')
                p.getUserSock().send(sMsg)

        def setupPlayerSockets(self):
                """
                TODO: purpose of the method

                {socket_object: ['socketType', 'userObject']}
                An example:
                     {socket_object_1: ['internet', 'user_object_1'],
                      socket_object_2: ['uds', 'user_object_2'],
                      socket_object_3: ['internet', 'user_object_3'],
                      socket_object_4: ['uds', 'user_object_4'],
                      socket_object_5: ['internet', 'user_object_5'],
                      socket_object_6: ['uds', 'user_object_6']}
                """
                READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
                self.poller = select.poll()
                self.sockListLock.acquire()
                e = []
                e.append('internet')
                e.append(self.p1)
                self.sockList[self.p1Sock] = e
                e = []
                e.append('uds')
                e.append(self.p1)
                self.sockList[self.p1UdsSock] = e
                e = []
                e.append('internet')
                e.append(self.p2)
                self.sockList[self.p2Sock] = e
                e = []
                e.append('uds')
                e.append(self.p2)
                self.sockList[self.p2UdsSock] = e

                for s in self.sockList:
                        self.fdToSocket[s.fileno()] = s
                        self.poller.register(s, READ_ONLY)
                self.sockListLock.release()

                #for p in self.playerList:
                        #e = []
        def setup(self):
                """
                TODO: purpose of the method
                """
                # Decide color and turn
                # Send SREQRP to both players
                self.decideTurn()
                self.decideColor()
                self.sendPlayResponse(self.p1, self.p1Color, self.playerList[self.p1])
                self.sendPlayResponse(self.p2, self.p2Color, self.playerList[self.p2])
                self.setupPlayerSockets()

        def cleanup(self):
                """
                TODO: purpose of the method
                """
                print('Game::cleanup')
                print('=============')
                self.sockListLock.acquire()
                for s in self.sockList:
                        uObject = self.sockList[s][1]
                        u = uObject.getUsername()
                        print(u + ': calling Event')
                        event = uObject.getEvent()
                        event.set()
                self.sockListLock.acquire()

        def destroyGame(self, uObject):
                """
                TODO: purpose of the method
                """
                #print('destroyGame')
                #print('===========')
                #
                # (1) send STEARD to all relevant parties (they are in sockList)
                # (2) wake up user threads of all relevant parties
                # (3) mark gameState as OVER so that a watcher who comes
                #         (a) gameList.removeGameFromGameList(self)
                #         (b) self.sockListLock.acquire()
                #     between a and b can be detected correctly
                #
                # No need to clean up sockList
                #
                gameList.removeGameFromGameList(self)
                self.sockListLock.acquire()
                self.gameState = 'OVER'
                sMsg = createTeardownMsg()
                #cSock = uObject.getUserSock() # already closed socket of the client
                for s in self.sockList:
                        if self.sockList[s][0] is 'internet':
                                #if s is not cSock:
                                try:
                                        s.send(sMsg)
                                except socket.error as err:
                                        #print(sMsg)
                                        #print(err)
                                        pass
                                uObject = self.sockList[s][1]
                                u = uObject.getUsername()
                                print(u + ': waking Up')
                                event = uObject.getEvent()
                                event.set()
                self.sockListLock.release()

        def removeWatcherFromPollingList(self, uObject):
                """
                TODO: purpose of the method
                """
                #print('removeWatcherFromPollingList')
                #print('============================')
                self.sockListLock.acquire()
                watcherSock = uObject.getUserSock()
                watcherUdsSock = uObject.getUserUdsSock()
                # socket might be removed polling list by
                try:
                        self.poller.unregister(watcherSock)
                except KeyError:
                        pass
                self.poller.unregister(watcherUdsSock)
                del self.fdToSocket[watcherSock.fileno()]
                del self.fdToSocket[watcherUdsSock.fileno()]
                del self.sockList[watcherSock]
                del self.sockList[watcherUdsSock]
                self.sockListLock.release()
                event = uObject.getEvent()
                event.set()
                print(uObject.getUsername() + ' is removed from the game: ' + self.gameName)

        def removeWatcher(self, s, uObject):
                """
                TODO: purpose of the method
                """
                #print('removeWatcher')
                #print('=============')
                sMsg = createSuccessResponseToLeaveRequest()
                s.send(sMsg)
                self.removeWatcherFromPollingList(uObject)

        def addWatcherToPollingList(self, uObject):
                """
                TODO: purpose of the method
                uObject: User object of watcher
                """
                #print('addWatcherToPollingList')
                #print('=======================')
                watcherSock = uObject.getUserSock()
                watcherUdsSock = uObject.getUserUdsSock()
                e = []
                e.append('internet')
                e.append(uObject)
                self.sockList[watcherSock] = e
                e = []
                e.append('uds')
                e.append(uObject)
                self.sockList[watcherUdsSock] = e
                self.fdToSocket[watcherSock.fileno()] = watcherSock
                self.fdToSocket[watcherUdsSock.fileno()] = watcherUdsSock
                READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
                self.poller.register(watcherSock, READ_ONLY)
                self.poller.register(watcherUdsSock, READ_ONLY)

        def addWatcher(self, uObject):
                """
                TODO: purpose of the method
                uObject: User object of watcher
                """
                #print('addWatcher')
                #print('==========')
                self.sockListLock.acquire()
                if self.gameState is 'OVER':
                        return False
                sMsg = createSuccessResponseToWatchRequest(self)
                uObject.getUserSock().send(sMsg)
                self.addWatcherToPollingList(uObject)
                ## TODO: may need to be added to watcherList
                self.sockListLock.release()
                print(uObject.getUsername() + ' is added to the game: ' + self.gameName)

        def handleUdsSockets(self, s, uObject):
                """
                TODO: purpose of the method
                """
                rMsg = s.recv(rUdsMsgSize)
                if rMsg == 'dead':
                        u = uObject.getUsername()
                        print(u + ' is dead')
                        userType = uObject.getUserType()
                        if userType == 'player':
                                self.destroyGame(uObject)
                                return True
                        elif userType == 'watcher':
                                self.removeWatcherFromPollingList(uObject)
                else:
                        print('unknown msg from Heartbeat')
                return False

        def throwDice(self):
                """
                TODO: purpose of the method
                """
                dice1 = random.choice(range(1, 7))
                dice2 = random.choice(range(1, 7))
                return (dice1, dice2)

        def sendBroadcastMsg(self, sMsg):
                """
                TODO: purpose of the method
                """
                self.sockListLock.acquire()
                for s in self.sockList:
                        s.send(sMsg)
                self.sockListLock.release()

        def handleGameLogic(self, rMsg, s, uObject):
                """
                TODO: purpose of the method
                """
                if self.gameState == 'DICE' and self.activePlayer != uObject:
                        # unrecognized message from the user
                        # send SVRNOK
                        uObject.sendSvrnokToClient(rMsg)
                else:
                         print('valid CTDICE')
                         print(rMsg)
                         # prepare STDICE msg
                         dice = self.throwDice()
                         sMsg = createServerThrowDiceMsg(dice[0], dice[1])
                         self.sendBroadcastMsg(sMsg)
                         #s.send(sMsg)


        def handleInternetSockets(self, s, uObject):
                """
                TODO: purpose of the method
                """
                rMsg = s.recv(rMsgSize)
                #print('handleInternetSockets: ', rMsg)
                header = getMsgHeader(rMsg)
                userType = uObject.getUserType()
                if header == 'CLPONG':
                        #print(self.gameName + ':CLPONG for ' + uObject.getUsername())
                        uObject.handlePongResponse(rMsg)
                elif header == 'CREQST' and userType is 'watcher':
                        paramDict = getMsgBody(rMsg)
                        request = paramDict['type']
                        if request != 'leave':
                                # unrecognized message from the user
                                # send SVRNOK
                                uObject.sendSvrnokToClient(rMsg)
                                return
                        self.removeWatcher(s, uObject)
                elif header == '' and (userType is 'watcher' or userType is 'player'):
                        # client socket is closed. Prepare to remove it
                        self.poller.unregister(s)
                elif s is self.p1Sock or s is self.p2Sock:
                        self.handleGameLogic(rMsg, s, uObject)
                else:
                        # client socket is closed. Prepare to remove it
                        # unrecognized message from the user
                        # send SVRNOK
                        uObject.sendSvrnokToClient(rMsg)

        def main_loop(self):
                """
                Main loop of a Game object/thread
                """
                # poll for unix domain socket and client socket of players and watchers
                #print('GAME:' + self.gameName + ' main_loop')
                out = False
                while True:
                        events = self.poller.poll()
                        for fd, flag in events:
                                self.sockListLock.acquire()
                                s = self.fdToSocket[fd]
                                socketType = self.sockList[s][0]
                                uObject = self.sockList[s][1]
                                self.sockListLock.release()
                                if flag & (select.POLLIN | select.POLLPRI):
                                        #
                                        # Unix Domain Sockets (uds) go here. Heartbeat object
                                        # uses uds and simply its treatment is roughly the same
                                        # for players and watchers except in the case that a
                                        # player loses its connection, which translates to
                                        # sending STEARD to all parties
                                        #
                                        if socketType == 'uds':
                                                if self.handleUdsSockets(s, uObject) is True:
                                                        out = True
                                                        break
                                        elif socketType == 'internet':
                                                self.handleInternetSockets(s, uObject)
                        #
                        # Leaving because
                        # (1) Game is over.
                        #     Send SGMOVR to all relevant parties
                        #
                        # (2) A player is lost his/her connection.
                        #     Send STEARD to all relevant parties
                        #
                        if out is True:
                                break

        def run(self):
                """
                Main thread of Game object
                """
                #print('Game starts')
                #print('===========')
                print('Game: ' + self.gameName + ' starts...')
                self.setup()

                # game is ready for being added to gameList
                gameList.addGameToGameList(self)

                # poll sockets of each player and also watchers
                self.main_loop()

                #self.cleanup()

        def getp1Username(self):
                """
                Return username of player 1
                """
                return self.p1Username

        def getp2Username(self):
                """
                Return username of player 2
                """
                return self.p2Username

        def getp1Color(self):
                """
                Returns color of player 1
                """
                return self.p1Color

        def getp2Color(self):
                """
                Returns color of player 2
                """
                return self.p2Color

        def getScore(self):
                """
                Return the score of the game
                """
                return self.score

        def getTurn(self):
                """
                Returns the username of the player whose turn to play
                """
                return self.activePlayer.getUsername()

        def getBoard(self):
                """
                TODO: purpose of the method
                """
                return self.board

class User(threading.Thread):
        """
        Representation of a backgammon user
        """

        def __init__(self, csock, addr, heartbeat, serverAddr=commServerAddr):
                """
                Constructor of User class
                csock: Client socket
                addr: client address in the form of a tuple (ip, port)
                heartbeat: Heartbeat object created by Server
                serverAddr = Unix Domain Socket address of CommServer, which is used
                by Heartbeat to send messages to User and Game classes
                """
                threading.Thread.__init__(self)
                self.userSock = csock
                self.addr = addr
                self.heartbeat = heartbeat
                self.serverAddr = serverAddr
                self.userUdsSock =-1
                self.userType = 'unknown'
                self.username = 'unknown'
                self.state = 'CONNECTING'
                self.event = Event()
                self.pongMissingCount = 0
                self.poller = -1
                self.fdToSocket = {}
                self.gameInitializer = False
                self.game = False
                self.heartbeatSent = False

        def setHeartbeatSent(self, val):
                """
                TODO: purpose of the method
                """
                self.heartbeatSent = val

        def getHeartbeatSent(self):
                """
                TODO: purpose of the method
                """
                return self.heartbeatSent

        def connectToCommServer(self):
                """
                TODO: purpose of the method
                """
                self.userUdsSock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.userUdsSock.connect(self.serverAddr)
                self.userUdsSock.send(self.username)
                #rMsg = self.userUdsSock.recv(rUdsMsgSize)
                #print('importante: ' + str(rMsg))
                # Sync with Heartbeat before going further
                self.event.wait()
                # let's clear it again in case it is used in the future
                self.event.clear()

        def handleLoginRequest(self):
                """
                Manages login requests coming from Clients/Users
                """
                print('Got connection from', self.addr)
                rMsg = self.userSock.recv(rMsgSize)
                #print(rMsg)
                if getMsgHeader(rMsg) != 'CLOGIN':
                        # unrecognized message from the user: send SVRNOK
                        self.sendSvrnokToClient(rMsg)
                        return False

                paramDict = getMsgBody(rMsg)
                self.username = paramDict.get('userid', None)
                if self.username is None or len(paramDict) > 1:
                        # unrecognized message from the user: send SVRNOK
                        self.sendSvrnokToClient(rMsg)
                        return False

                userListLock.acquire()
                if userList.get(self.username, None) is None:
                        userEntry = []
                        userEntry.append(self)
                        userList[self.username] = userEntry
                        result = True
                else:
                        result = False
                userListLock.release()
                if result is True:
                        sMsg = createSuccessResponseToLoginRequest()
                        print('OK: ' + str(self.username) +
                              '. You are logged in to the server')
                else:
                        sMsg = createFailResponseToLoginRequest()
                        print('FAIL: ' + str(self.username) + ' already exists.')
                self.userSock.send(sMsg)
                if result is False:
                        return False
                return True

        def main_loop(self):
                """
                Main loop of a User object/thread
                """
                # poll for unix domain socket and client socket
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
                                                msg = self.userUdsSock.recv(rUdsMsgSize)
                                                if msg == 'dead':
                                                        waitingRoom.markAsInvalid(self.username)
                                                        print(self.username + ' is dead')
                                                        out = True
                                                        break
                                                else:
                                                        print('unknown msg from Heartbeat')
                                        elif s is self.userSock:
                                                self.handleUserMsg()
                                                if self.state is 'LEAVING':
                                                        waitingRoom.markAsInvalid(self.username)
                                                        out = True
                                                        break
                                if self.state is 'PLAYING' or self.state is 'WATCHING':
                                        #
                                        # control will be given to Game
                                        # self.state is set to PLAYING by another thread and
                                        # it's asynchronous.
                                        #
                                        # After active thread disables polling for itself,
                                        # passive thread (waiting to play a game) is informed
                                        # by setting its state to 'PLAYING'. During this time,
                                        # active thread waits for passive thread to set an event.
                                        # This event object belongs to passive thread. This is
                                        # because passive player should disable polling on its
                                        # own. Otherwise, if active thread disabled polling, it
                                        # would cause sync problems
                                        #
                                        # self.state is set to WATCHING by thread's itself
                                        #
                                        if self.userType is 'player' and self.gameInitializer is False:
                                                self.disablePolling()
                                                #print(self.username + ': waking up the opponent')
                                                self.event.set()
                                        out = True
                                        break
                        #
                        # Leaving because
                        # (1) self.state is 'CONNECTED'.
                        #     user did not respond to SVPING requests.
                        #     In this case, self.userSock is still polled
                        #
                        # (2) self.state is 'CONNECTED'
                        #     we noticed that client closed his/her socket
                        #     before SVPING/CLPONG sequence does its job.
                        #     In this case, self.userSock is already removed
                        #     from the polling list by handleUserMsg
                        #
                        # (3) self.state is 'WAITING'
                        #     user send a leave request while waiting an opponent
                        #     self.userSock is already in the polling list. Same
                        #     with (2)
                        #     Also tell the waitingRoom that user should be marked as 'deleted'
                        #
                        # (4) self.state is 'PLAYING'
                        #     We were in the waitingRoom. Another user came in to play
                        #     and found us in waitingRoom. That user wants to let us
                        #     know that we will be having a game by setting our state to
                        #     'PLAYING'. When we notice this, we disable polling and let the
                        #     other thread know it, which was waiting us after setting our
                        #     state to 'PLAYING'.
                        #
                        # (5) self.state is 'WATCHING'
                        #     A watcher is added to a game's list of watchers. From now on,
                        #     Game object handles watcher's requests, which may only be a
                        #     'leave' request
                        #
                        if out is True:
                                break

        def run(self):
                """
                Main thrad of User object
                """
                # Handle login request coming from the client
                if self.handleLoginRequest() is False:
                        self.userSock.close()
                        return

                # Connect to CommServer to get a Unix Domain Socket
                # This is needed for Heartbeat object send a message to us
                # The only message is 'dead', which shows that this client
                # didn't respond to 2-back-back ping message
                self.connectToCommServer()
                self.state = 'CONNECTED'

                # poll for unix domain socket and client socket
                self.main_loop()

                if self.state is not 'PLAYING' and self.state is not 'WATCHING':
                        if self.state is 'LEAVING':
                                sMsg = createSuccessResponseToLeaveRequest()
                                try:
                                        self.userSock.send(sMsg)
                                except socket.error as err:
                                        #print(sMsg)
                                        #print(err)
                                        pass
                        self.cleanup()
                        return

                # 'PLAYING' or 'WATCHING' state
                print(self.username + ': waiting Game to be over')
                # wait Game to be over
                self.event.clear()
                self.event.wait()
                print(self.username + ': Game is over')
                #self.state = 'UNKNOWN'
                #if self.gameInitializer is True:
                        #gameList.removeGameFromGameList(self.game)
                self.closeSockets()
                self.removeUserFromUserList()

        def disablePolling(self):
                """
                TODO: purpose of the method
                """
                #for entry in self.fdToSocket:
                        #sock = self.fdToSocket[entry]
                        #try:
                                #self.poller.unregister(sock)
                        #except KeyError:
                                #pass
                for entry in self.fdToSocket:
                        sock = self.fdToSocket[entry]
                        self.poller.unregister(sock)
                # It's not a good idea to remove from dict while iterating
                # 2 items to remove. Don't bother it
                self.fdToSocket.pop(self.userSock.fileno(), None)
                self.fdToSocket.pop(self.userUdsSock.fileno(), None)

        def removeUserFromUserList(self):
                """
                TODO: purpose of the method
                """
                userListLock.acquire()
                u = userList.pop(self.username, None)
                if u is None:
                        print(self.username + 'is not in userList')
                        print('Points to a possible bug in Server software')
                userListLock.release()

        def closeSockets(self):
                """
                TODO: purpose of the method
                """
                self.userSock.close()
                self.userUdsSock.close()

        def cleanup(self):
                """
                TODO: purpose of the method
                """
                self.disablePolling()
                self.closeSockets()
                self.removeUserFromUserList()

        def sendSvrnokToClient(self, rMsg):
                """
                TODO: purpose of the method
                """
                print('Server: unrecognized msg from the client')
                print('<BEGIN>')
                print(rMsg)
                print('</END>')
                sMsg = createSvrnokMsg()
                #print(sMsg)
                self.userSock.send(sMsg)

        def handlePlayRequest(self):
                """
                TODO: purpose of the method
                """
                #print('handlePlayRequest')
                #print('=================')
                self.userType = 'player'
                #
                # A player whose name is the same with this player, might be put into
                # waiting room before. If we don't make that entry valid again, WaitingRoom
                # will think that it is invalid
                #
                #waitingRoom.markAsValid(self.username)
                opponent = waitingRoom.getOpponent(self.username)
                if opponent is False:
                        # No opponent to play
                        # put user to waitingRoom and set state to WAITING
                        #print('no opponent to play')
                        waitingRoom.addToWaitingRoom(self.username)
                        self.state = 'WAITING'
                        # send SREQRP play(fail) message to the user
                        sMsg = createFailResponseToPlayRequest()
                        self.userSock.send(sMsg)
                        return
                #print('opponent to play: ' + opponent)
                # success
                #print('there is an opponent to play')
                userListLock.acquire()
                opponent = userList[opponent][0]
                userListLock.release()
                #
                # tell User thread not to listen any socket.
                # It should just wait Game to be over
                #
                self.gameInitializer = True
                self.disablePolling()
                self.state = 'PLAYING'
                self.userType = 'player'
                opponent.setUserType('player')
                # wait opponent Thread to stop polling
                # setting opponentState to 'PLAYING' is enough
                #opponent.disablePolling()
                #print(self.username + ': waiting opponent...')
                event = opponent.getEvent()
                opponent.setState('PLAYING')
                event.wait()
                #print(self.username + ': woken up...')
                # create Game object and add it to gameList
                g = Game(self, opponent)
                self.game = g
                #gameList.addGameToGameList(g)
                g.start()

        def handleWatchRequest(self):
                """
                TODO: purpose of the method
                """
                #print('handleWatchRequest')
                #print('==================')
                #self.sendSvrnokToClient('watch')
                # find a match to watch
                game = gameList.findGame()
                if game == None:
                        # there is no match to watch. Send SREQRP watch(fail)
                        sMsg = createFailResponseToWatchRequest()
                        self.userSock.send(sMsg)
                        return
                # There is a match to watch
                #print(self.username + ': there is a game to watch')
                self.state = 'WATCHING'
                self.userType = 'watcher'
                self.disablePolling()
                game.addWatcher(self)

        def handleClientRequest(self, rMsg):
                """
                TODO: purpose of the method
                """
                paramDict = getMsgBody(rMsg)
                request = paramDict['type']
                print(self.username + ' request is ' + request)
                if request == 'play' and self.state == 'CONNECTED':
                        self.handlePlayRequest()
                elif request == 'watch' and self.state == 'CONNECTED':
                        self.handleWatchRequest()
                elif request == 'leave' and self.state == 'WAITING':
                        print(self.username + ' wants to leave')
                        # Mark the client as leaving. It will be handled in the main loop
                        self.state = 'LEAVING'
                else:
                        print('unrecognized CREQST msg from client')
                        self.sendSvrnokToClient(rMsg)

        def handleUserMsg(self):
                """
                TODO: purpose of the method
                """
                rMsg = self.userSock.recv(rMsgSize)
                #print('handleUserMsg: ', rMsg)
                header = getMsgHeader(rMsg)
                if header == 'CLPONG':
                        self.handlePongResponse(rMsg)
                elif header == 'CREQST':
                        self.handleClientRequest(rMsg)
                elif header == '':
                        # client socket is closed. Prepare to remove it
                        self.poller.unregister(self.userSock)
                        self.fdToSocket.pop(self.userSock.fileno())
                else:
                        # unrecognized message from the user
                        # send SVRNOK
                        self.sendSvrnokToClient(rMsg)

        def handlePongResponse(self, rMsg):
                """
                TODO: purpose of the method
                """
                global clientPongWinOpen
                paramDict = {}
                #print(rMsg)
                paramDict = getMsgBody(rMsg)
                #print(paramDict)
                if clientPongWinOpen is True:
                        self.pongMissingCount = -1
                        #print(self.username + ': handlePongResponse: ' + paramDict["msgId"])
                #else:
                        #print('GayyaKuyusu: ' + self.username + ': handlePongResponse: ' + paramDict["msgId"])

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

        def getUserUdsSock(self):
                """
                TODO: purpose of the method
                """
                return self.userUdsSock

        def getUsername(self):
                """
                TODO: purpose of the method
                """
                return self.username

        def getUserType(self):
                """
                TODO: purpose of the method
                """
                return self.userType

        def setUserType(self, userType):
                """
                TODO: purpose of the method
                """
                self.userType = userType

        def getState(self, state):
                """
                TODO: purpose of the method
                """
                return self.state

        def setState(self, state):
                """
                TODO: purpose of the method
                """
                self.state = state

        def getEvent(self):
                """
                TODO: purpose of the method
                """
                return self.event

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
        waitingRoom = WaitingRoom()
        gameList = GameList()
        s = Server()
        s.run()
