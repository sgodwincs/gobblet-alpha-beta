import sys
import random
import copy
import sched
import time
from collections import OrderedDict
from enum import Enum

infinity = sys.maxsize

class Level(Enum):
    Beginner = 0
    Intermediate = 1
    Expert = 2

class PlayerRule(Enum):
    HumanHuman = 1
    HumanRobot = 2
    RobotHuman = 3
    RobotRobot = 4

class GameState(object):
    BOARD_HEIGHT = 4
    BOARD_WIDTH = 4
    GOBBLETS_PER_STACK = 4
    NUMBER_OF_GOBBLETS = 12
    NUMBER_OF_PLAYERS = 2
    NUMBER_OF_STACKS = 3
    NUMBER_OF_WAYS_TO_WIN = 10
    TYPES_OF_GOBBLETS = 4

    def __init__(self, moveTime):
        self.gobblets = [ ]
        self.stacks = [ ]
        self.board = [ ]
        self.scores = [ ]
        self.turn = 0
        self.moveNumber = 1
        self.moveTime = moveTime

        for i in range(GameState.BOARD_HEIGHT):
            self.board.append([ ])

            for j in range(GameState.BOARD_WIDTH):
                self.board[i].append([ ])

        for i in range(GameState.NUMBER_OF_WAYS_TO_WIN):
            self.scores.append(0)

        for i in range(GameState.NUMBER_OF_PLAYERS):
            self.gobblets.append([ ])
            self.stacks.append([ ])

            for j in range(GameState.NUMBER_OF_STACKS):
                self.stacks[-1].append([ ])

            stackPosition = 0

            for j in range(GameState.NUMBER_OF_GOBBLETS):
                self.gobblets[i].append(((j % GameState.TYPES_OF_GOBBLETS) + 1, True, stackPosition, len(self.stacks[i][stackPosition])))
                self.stacks[i][stackPosition].append(len(self.gobblets[-1]) - 1)

                if len(self.stacks[i][stackPosition]) >= GameState.GOBBLETS_PER_STACK:
                    stackPosition += 1

    def __eq__(self, other):
        return self.gobblets == other.gobblets

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.turn, tuple(self.gobblets[0]), tuple(self.gobblets[1])))

    def __str__(self):
        string = ''

        if self.moveNumber > 1:
            string += '=' * 15 + '\n'

        string += 'Move: ' + str(self.moveNumber) + '\n\n'

        for i in range(GameState.NUMBER_OF_PLAYERS):
            string += 'Player ' + str(i + 1) + ' Available Off-board Gobblets: '

            for stack in self.stacks[i]:
                if len(stack) > 0:
                    string += self.gobbletToString(i, stack[-1]) + ' '

            string += '\n'

        string += '\n'

        for i, row in enumerate(self.board):
            for j, stack in enumerate(row):
                if len(stack) == 0:
                    string += ' ' * 9
                else:
                    string += self.gobbletToString(stack[-1][0], stack[-1][1])

                if j != len(row) - 1:
                    string += '|'

            string += '\n'

            if i != len(self.board) - 1:
                for j in range(GameState.BOARD_WIDTH * 9 + GameState.BOARD_WIDTH - 1):
                    string += '-'

                string += '\n'

        string += '\n\n'

        if not self.isTerminal():
            string += 'Player {}\'s turn ({} seconds to move)'.format(self.turn + 1, self.moveTime * 60)

        return string

    def getNextGameState(self, action):
        self.handleAction(action)
        self.turn = (self.turn + 1) % GameState.NUMBER_OF_PLAYERS
        self.moveNumber += 1

        return self

    def getPrevGameState(self, action):
        self.turn = (self.turn + 1) % GameState.NUMBER_OF_PLAYERS
        self.moveNumber -= 1
        self.handleAction(action)
        return self

    def getMaxScore(self):
        maxScore = 0

        for score in self.scores:
            if abs(score) > abs(maxScore):
                maxScore = score

        return maxScore

    def contains3InARow(self, player, point):
        if len(self.board[point[0]][point[1]]) == 0 or \
            not self.board[point[0]][point[1]][0][0] == player:
            return False

        # Horizontal.

        if point[0] - 2 >= 0 and \
            len(self.board[point[0] - 2][point[1]]) > 0 and \
            len(self.board[point[0] - 1][point[1]]) > 0 and \
            self.board[point[0] - 2][point[1]][0][0] == player and \
            self.board[point[0] - 1][point[1]][0][0] == player:
            return True

        if point[0] - 1 >= 0 and point[0] + 1 < GameState.BOARD_WIDTH and \
            len(self.board[point[0] - 1][point[1]]) > 0 and \
            len(self.board[point[0] + 1][point[1]]) > 0 and \
            self.board[point[0] - 1][point[1]][0][0] == player and \
            self.board[point[0] + 1][point[1]][0][0] == player:
            return True

        if point[0] + 2 < GameState.BOARD_WIDTH and \
            len(self.board[point[0] + 1][point[1]]) > 0 and \
            len(self.board[point[0] + 2][point[1]]) > 0 and \
            self.board[point[0] + 1][point[1]][0][0] == player and \
            self.board[point[0] + 2][point[1]][0][0] == player:
            return True

        # Vertical

        if point[1] - 2 >= 0 and \
            len(self.board[point[0]][point[1] - 2]) > 0 and \
            len(self.board[point[0]][point[1] - 1]) > 0 and \
            self.board[point[0]][point[1] - 2][0][0] == player and \
            self.board[point[0]][point[1] - 1][0][0] == player:
            return True

        if point[1] - 1 >= 0 and point[1] + 1 < GameState.BOARD_HEIGHT and \
            len(self.board[point[0]][point[1] - 1]) > 0 and \
            len(self.board[point[0]][point[1] + 1]) > 0 and \
            self.board[point[0]][point[1] - 1][0][0] == player and \
            self.board[point[0]][point[1] + 1][0][0] == player:
            return True

        if point[1] + 2 < GameState.BOARD_HEIGHT and \
            len(self.board[point[0]][point[1] + 1]) > 0 and \
            len(self.board[point[0]][point[1] + 2]) > 0 and \
            self.board[point[0]][point[1] + 1][0][0] == player and \
            self.board[point[0]][point[1] + 2][0][0] == player:
            return True

        # Diagonal

        if point[0] - 2 >= 0 and point[1] - 2 >= 0 and \
            len(self.board[point[0] - 2][point[1] - 2]) > 0 and \
            len(self.board[point[0] - 1][point[1] - 1]) > 0 and \
            self.board[point[0] - 2][point[1] - 2][0][0] == player and \
            self.board[point[0] - 1][point[1] - 1][0][0] == player:
            return True

        if point[0] - 1 >= 0 and point[1] - 1 >= 0 and \
            point[0] + 1 < GameState.BOARD_WIDTH and point[1] + 1 < GameState.BOARD_HEIGHT and \
            len(self.board[point[0] - 1][point[1] - 1]) > 0 and \
            len(self.board[point[0] + 1][point[1] + 1]) > 0 and \
            self.board[point[0] - 1][point[1] - 1][0][0] == player and \
            self.board[point[0] + 1][point[1] + 1][0][0] == player:
            return True

        if point[0] + 2 < GameState.BOARD_WIDTH and point[1] + 2 < GameState.BOARD_HEIGHT and \
            len(self.board[point[0] + 2][point[1] + 2]) > 0 and \
            len(self.board[point[0] + 1][point[1] + 1]) > 0 and \
            self.board[point[0] + 2][point[1] + 2][0][0] == player and \
            self.board[point[0] + 1][point[1] + 1][0][0] == player:
            return True

        if point[0] - 2 >= 0 and point[1] + 2 < GameState.BOARD_HEIGHT and \
            len(self.board[point[0] - 2][point[1] + 2]) > 0 and \
            len(self.board[point[0] - 1][point[1] + 1]) > 0 and \
            self.board[point[0] - 2][point[1] + 2][0][0] == player and \
            self.board[point[0] - 1][point[1] + 1][0][0] == player:
            return True

        if point[0] - 1 >= 0 and point[1] + 1 < GameState.BOARD_HEIGHT and \
            point[0] + 1 < GameState.BOARD_WIDTH and point[1] - 1 >= 0 and \
            len(self.board[point[0] - 1][point[1] + 1]) > 0 and \
            len(self.board[point[0] + 1][point[1] - 1]) > 0 and \
            self.board[point[0] - 1][point[1] + 1][0][0] == player and \
            self.board[point[0] + 1][point[1] - 1][0][0] == player:
            return True

        if point[0] + 2 < GameState.BOARD_WIDTH and point[1] - 2 >= 0 and \
            len(self.board[point[0] + 2][point[1] - 2]) > 0 and \
            len(self.board[point[0] + 1][point[1] - 1]) > 0 and \
            self.board[point[0] + 2][point[1] - 2][0][0] == player and \
            self.board[point[0] + 1][point[1] - 1][0][0] == player:
            return True

        return False

    def getAvailableActions(self):
        actions = [ ]
        currentPlayer = self.turn
        nextPlayer = (self.turn + 1) % GameState.NUMBER_OF_PLAYERS

        for i, gobblet in enumerate(self.gobblets[currentPlayer]):
            offBoard = False

            if gobblet[1]:
                if gobblet[3] != len(self.stacks[currentPlayer][gobblet[2]]) - 1:
                    continue

                offBoard = True

            stack = self.board[gobblet[2]][gobblet[3]]

            if offBoard or (stack[-1][0] == currentPlayer and stack[-1][1] == i):
                for j, row in enumerate(self.board):
                    for k, stack in enumerate(row):
                        baseCondition = len(stack) == 0 or gobblet[0] > self.gobblets[currentPlayer][stack[-1][1]][0]

                        if not baseCondition:
                            continue

                        if not offBoard or len(stack) == 0 or self.contains3InARow(nextPlayer, (j, k)):
                            actions.append((i, (j, k), False))

        return actions

    def getReversedAction(self, action):
        gobblet = self.gobblets[self.turn][action[0]]
        return (action[0], (gobblet[2], gobblet[3]), gobblet[1])

    def handleAction(self, action):
        currentPlayer = self.turn
        nextPlayer = (currentPlayer + 1) % GameState.NUMBER_OF_PLAYERS
        gobblet = self.gobblets[currentPlayer][action[0]]
        destination = action[1]

        # Update scores.

        if currentPlayer == 0:
            winValue = 1
            lossValue = -1
        else:
            winValue = -1
            lossValue = 1

        if not gobblet[1]:
            stack = self.board[gobblet[2]][gobblet[3]]

            if len(stack) > 1:
                if stack[-2][0] == nextPlayer:
                    lossValue *= 2
                else:
                    lossValue = 0

            self.scores[gobblet[2]] += lossValue
            self.scores[gobblet[3] + GameState.BOARD_WIDTH] += lossValue

            if gobblet[2] == gobblet[3]:
                self.scores[GameState.BOARD_WIDTH * 2] += lossValue

            if gobblet[2] == (GameState.BOARD_HEIGHT - gobblet[3] - 1):
                self.scores[GameState.BOARD_WIDTH * 2 + 1] += lossValue

        if not action[2]:
            stack = self.board[destination[0]][destination[1]]

            if len(stack) > 0:
                if stack[-1][0] == nextPlayer:
                    winValue *= 2
                else:
                    winValue = 0

            self.scores[destination[0]] += winValue
            self.scores[destination[1] + GameState.BOARD_WIDTH] += winValue

            if destination[0] == destination[1]:
                self.scores[GameState.BOARD_WIDTH * 2] += winValue

            if destination[0] == (GameState.BOARD_HEIGHT - destination[1] - 1):
                self.scores[GameState.BOARD_WIDTH * 2 + 1] += winValue

            if gobblet[1]:
                self.stacks[currentPlayer][gobblet[2]].pop()
            else:
                self.board[gobblet[2]][gobblet[3]].pop()

            self.board[destination[0]][destination[1]].append((currentPlayer, action[0]))
        else:
            if not gobblet[1]:
                self.board[gobblet[2]][gobblet[3]].pop()

            self.stacks[currentPlayer][action[1][0]].append(action[0])

        self.gobblets[currentPlayer][action[0]] = (gobblet[0], action[2], destination[0], destination[1])

    def gobbletToString(self, player, index):
        return 'P' + str(player + 1) + '-G' + str(index).zfill(2) + '-S' + str(self.gobblets[player][index][0])

    def isTerminal(self):
        maxScore = self.getMaxScore()
        return maxScore == 4 or maxScore == -4

class HumanController(object):
    def pickAction(self, gameState):
        actions = gameState.getAvailableActions()

        while True:
            actionInput = input('Your move (a to (i, j)): ').strip()
            parts = actionInput.split(' ', 2)

            if len(parts) < 3 or parts[1].lower() != 'to':
                print('Invalid format.')
                continue

            destinationParts = parts[2].replace(' ', '').split(',')

            if len(destinationParts) != 2 or destinationParts[0] == '' or destinationParts[1] == '':
                print('Invalid format.')
                continue

            tmp = destinationParts[1]
            destinationParts[1] = destinationParts[0][-1] + ')'
            destinationParts[0] = '(' + tmp[0]
            parts[2] = ','.join(destinationParts)

            for action in actions:
                if parts[0].lower() == gameState.gobbletToString(gameState.turn, action[0]).lower() and \
                    parts[2].lower() == str(action[1]).lower().replace(' ', ''):
                    return action

            print('Invalid gobblet/destination.')

class RobotController(object):
    WAYS_TO_WIN = 10
    WIN_ARRAY = [
        [ (0, 0), (0, 1), (0, 2), (0, 3) ],
        [ (1, 0), (1, 1), (1, 2), (1, 3) ],
        [ (2, 0), (2, 1), (2, 2), (2, 3) ],
        [ (3, 0), (3, 1), (3, 2), (3, 3) ],
        [ (0, 0), (1, 0), (2, 0), (3, 0) ],
        [ (0, 1), (1, 1), (2, 1), (3, 1) ],
        [ (0, 2), (1, 2), (2, 2), (3, 2) ],
        [ (0, 3), (1, 3), (2, 3), (3, 3) ],
        [ (0, 0), (1, 1), (2, 2), (3, 3) ],
        [ (0, 3), (1, 2), (2, 1), (3, 0) ]
    ]

    VALUE_ARRAY = [
        [  0, -1, -2, -3, -1000 ],
        [  1,  0, -1, -2,  0 ],
        [  2,  1,  0, -1,  0 ],
        [  3,  2,  1,  0,  0 ],
        [ 1000, 0,  0,  0,  0 ]
    ]

    def __init__(self, playerIndex, moveTime, level):
        self.playerIndex = playerIndex
        self.moveTime = moveTime

        if level == Level.Beginner:
            self.maxDepth = 3
        elif level == Level.Intermediate:
            self.maxDepth = 6
        elif level == Level.Expert:
            self.maxDepth = 7

    def evaluate(self, gameState):
        board = gameState.board
        valueSum = 0

        for i in range(RobotController.WAYS_TO_WIN):
            p1Count = 0
            p2Count = 0

            for j in range(4):
                point = RobotController.WIN_ARRAY[i][j]
                nodeStack = board[point[0]][point[1]]

                if len(nodeStack) > 0:
                    if nodeStack[-1][0] == self.playerIndex:
                        p1Count += 1
                    else:
                        p2Count += 1

            valueSum += RobotController.VALUE_ARRAY[p1Count][p2Count]

        return valueSum

    def isCutoff(self, gameState, depth):
        return depth <= 0 or gameState.isTerminal()

    def maxValue(self, gameState, depth, alpha, beta):
        self.scheduler.run(False)

        if self.timeOver:
            return 0

        if self.isCutoff(gameState, depth):
            return self.evaluate(gameState)

        resultValue = -sys.maxsize - 1

        for action in gameState.getAvailableActions():
            reverseAction = gameState.getReversedAction(action)
            resultValue = max(resultValue, self.minValue(gameState.getNextGameState(action), depth - 1, alpha, beta))
            gameState.getPrevGameState(reverseAction)

            if resultValue >= beta:
                return resultValue

            alpha = max(alpha, resultValue)

        return resultValue

    def minValue(self, gameState, depth, alpha, beta):
        self.scheduler.run(False)

        if self.timeOver:
            return 0

        if self.isCutoff(gameState, depth):
            return self.evaluate(gameState)

        resultValue = sys.maxsize

        for action in gameState.getAvailableActions():
            reverseAction = gameState.getReversedAction(action)
            resultValue = min(resultValue, self.maxValue(gameState.getNextGameState(action), depth - 1, alpha, beta))
            gameState.getPrevGameState(reverseAction)

            if resultValue <= alpha:
                return resultValue

            beta = min(beta, resultValue)

        return resultValue

    def timeOverEvent(self):
        self.timeOver = True

    def pickAction(self, gameState):
        savedBestActions = [ ]
        actions = gameState.getAvailableActions()
        self.timeOver = False
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(self.moveTime * 60, 1, self.timeOverEvent)
        self.scheduler.run(False)

        for depth in range(1, self.maxDepth):
            actionValues = { }
            bestValue = -infinity
            bestActions = [ ]

            for action in actions:
                reverseAction = gameState.getReversedAction(action)
                value = self.minValue(gameState.getNextGameState(action), depth - 1, -infinity, infinity)
                gameState.getPrevGameState(reverseAction)
                actionValues[action] = value

                if value > bestValue:
                    bestValue = value
                    bestActions = [ action ]
                elif value == bestValue:
                    bestActions.append(action)

                if bestValue > 900:
                    break

            if self.timeOver:
                break

            savedBestActions = copy.deepcopy(bestActions)

            if bestValue > 900:
                break

            actions.sort(key=lambda x: actionValues[x], reverse=True)

        return savedBestActions[random.randint(0, len(savedBestActions) - 1)]

class Game(object):
    def __init__(self, playerRule, level, moveTime):
        self.playerRule = playerRule
        self.controllers = [ ]
        self.moveHistory = [ ]
        self.gameStateHash = set()

        players = [ ]

        if playerRule == PlayerRule.HumanHuman:
            self.controllers.append(HumanController())
            self.controllers.append(HumanController())
        elif playerRule == PlayerRule.HumanRobot:
            self.controllers.append(HumanController())
            self.controllers.append(RobotController(1, moveTime, level))
        elif playerRule == PlayerRule.RobotHuman:
            self.controllers.append(RobotController(0, moveTime, level))
            self.controllers.append(HumanController())
        else:
            self.controllers.append(RobotController(0, moveTime, level))
            self.controllers.append(RobotController(1, moveTime, level))

        self.currentState = GameState(moveTime)

    def run(self):
        while not self.currentState.isTerminal():
            print(self.currentState)

            if self.currentState in self.gameStateHash:
                print('Game state repeated. Game is a draw!')
                return list(map(lambda x : (x[0], x[1]), self.moveHistory))

            self.gameStateHash.add(self.currentState)
            action = self.controllers[self.currentState.turn].pickAction(self.currentState)
            self.moveHistory.append(action)
            self.currentState.getNextGameState(action)

        print(self.currentState)

        if self.currentState.getMaxScore() == 4:
            print('Player 1 won!')
        else:
            print('Player 2 won!')

        return list(map(lambda x : (x[0], x[1]), self.moveHistory))

def gobby(playerRule, level, moveTime):
    return Game(playerRule, level, moveTime).run()

print(gobby(PlayerRule.RobotRobot, Level.Beginner, .5))
