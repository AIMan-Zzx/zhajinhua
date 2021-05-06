import collections
from random import shuffle
import numpy as np
from copy import copy, deepcopy

class Card:
    def __init__(self, suit, rank):
        self._suit = suit
        self._rank = rank
        self._value = Poker.ranks.index(rank) * 10 + Poker.suits.index(suit)

    def __str__(self):
        return self._suit + self._rank

    def __lt__(self, other):
        return self.getValue() < other.getValue()

    def getSuit(self):
        return self._suit

    def getRank(self):
        return self._rank

    def getValue(self):
        return self._value

    def getSuitIndex(self):
        return self._value % 10 + 1

    def getRankIndex(self):
        return self._value // 10 + 1

class Poker:
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['♦', '♥', '♣', '♠']

    def __init__(self):
        self._cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def __len__(self):
        return len(self._cards)

    def __getitem__(self, position):
        return self._cards[position]

    def shuffle(self):
        shuffle(self._cards)

    def cut(self):
        print('Poker has been cut.')

    def reset(self):
        self._cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def showAllCard(self):
        [print(card) for card in self._cards]

class Player:
    def __init__(self, name, money=0):
        self._name = name
        self._money = money
        self.init_money = money
        self._currentGame = None
        self._currentIndex = None

    def getName(self):
        return self._name

    def shufflePoker(self):
        self._currentGame.shuffle()
        # print("Player " + self._name + ' has shuffled poker.')

    def enterGame(self, game, index):
        self._currentGame = game
        self._currentIndex = index
        # print('Player ' + self._name + ' has entered game !')

    def call(self):
        chip = self._currentGame.recall(self._currentIndex)
        self._money -= chip
        # print('%s call %d' % (self._name, chip))

    def quit(self):
        self._currentGame.reQuit(self._currentIndex)
        # print('%s quit' % self._name)

    def Raise(self, rate=2):
        chip = self._currentGame.reRaise(self._currentIndex, rate)
        self._money -= chip
        # print('%sraise%d' % (self._name, chip))

    def flop(self):
        cardsStr = self._currentGame.reFlop(self._currentIndex)
        # print('your cards is: ' + cardsStr)

    def Solo(self,opponetIndex):
        # opponetIndex = (self._currentIndex + 1)%self._currentGame.num_players
        chip = self._currentGame.reSolo(self._currentIndex,opponetIndex)
        self._money -= chip


    def winGame(self, money):
        self._money += money
        # print('win ',self._money-self.init_money-1)

    def payoff(self):
        return self._money - self.init_money

class Pair:
    def __init__(self, cards=[]):
        self._cards = cards
        self.sortPair()
        self._value = self._getValue()

    def __str__(self):
        return ', '.join([str(card) for card in self._cards])

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __le__(self, other):
        return self.__hash__() < other.__hash__()

    def sortPair(self):
        self._cards = sorted(self._cards)

    def getClusterClass(self):
        if self.isBaoZi():
            return 0
        if self.isShunZi():
            if self.isJinHua():
                return 0
            else:
                card_rank = self._cards[2]._rank
                index = Poker.ranks.index(card_rank)
                if index > 8:
                    return 3
                else:
                    return 4
        if self.isJinHua():
            card_rank = self._cards[2]._rank
            index = Poker.ranks.index(card_rank)
            if index > 8:
                return 1
            else:
                return 2
        if self.isDuiZi():
            if self._cards[0].getRankIndex() == self._cards[1].getRankIndex():
                card_rank = self._cards[0]._rank
                index = Poker.ranks.index(card_rank)
                if index > 9:
                    return 5
                elif index > 6:
                    return 6
                else:
                    return 7
            else:
                card_rank = self._cards[2]._rank
                index = Poker.ranks.index(card_rank)
                if index > 9:
                    return 5
                elif index > 6:
                    return 6
                else:
                    return 7
        else:
            card_rank = self._cards[2]._rank
            index = Poker.ranks.index(card_rank)
            if index == 12:
                return 8
            elif index > 8:
                return 9
            else:
                return 10

    def _getValue(self):
        if self.isBaoZi():
            return self._cards[2].getRankIndex() * 16 ** 7
        if self.isShunZi():
            if self._cards[0].getRankIndex() + 2 == self._cards[2]:
                if self.isShunJin():
                    return self._cards[2].getRankIndex() * 16 ** 6 + \
                           self._cards[1].getRankIndex() * 16 ** 5 + self._cards[2].getRankIndex() * 16 ** 4
                else:
                    return self._cards[2].getRankIndex() * 16 ** 4 + \
                           self._cards[1].getRankIndex() * 16 ** 3 + self._cards[2].getRankIndex() * 16 ** 2
            else:
                if self.isShunJin():
                    return 2 * 16 ** 6 + 1 * 16 ** 5 + 13 * 16 ** 4
                else:
                    return 2 * 16 ** 4 + 1 * 16 ** 3 + 13 * 16 ** 2
        if self.isJinHua():
            return self._cards[2].getRankIndex() * 16 ** 5 + \
                   self._cards[1].getRankIndex() * 16 ** 4 + self._cards[0].getRankIndex() * 16 ** 3
        if self.isDuiZi():
            if self._cards[0].getRankIndex() == self._cards[1].getRankIndex():
                return self._cards[0].getRankIndex() * 16 ** 3 + self._cards[2].getRankIndex() * 16 ** 2
            else:
                return self._cards[2].getRankIndex() * 16 ** 3 + self._cards[0].getRankIndex() * 16 ** 2
        else:
            return self._cards[2].getRankIndex() * 16 ** 2 + \
                   self._cards[1].getRankIndex() * 16 + self._cards[0].getRankIndex()

    def getValue(self):
        return self._value

    def isBaoZi(self):
        return self._cards[0].getRankIndex() == self._cards[2].getRankIndex()

    def isJinHua(self):
        return self._cards[0].getSuitIndex() == self._cards[1].getSuitIndex() \
               and self._cards[1].getSuitIndex() == self._cards[2].getSuitIndex()

    def isShunZi(self):
        index0 = Poker.ranks.index(self._cards[0]._rank)
        index1 = Poker.ranks.index(self._cards[1]._rank)
        index2 = Poker.ranks.index(self._cards[2]._rank)
        return (index0 + 2 == index2 and index0 + 1 == index1) or \
               (index0 == 0 and index1 == 1 and index2 == 12)
        # return self._cards[0].getRankIndex() + 2 == self._cards[2].getRankIndex() or \
        #        (self._cards[0].getRankIndex() == 0 and self._cards[1].getRankIndex() == 1
        #         and self._cards[2].getRankIndex() == 13)

    def isShunJin(self):
        return self.isJinHua() and self.isShunZi()

    def isDuiZi(self):
        return (self._cards[0].getRankIndex() == self._cards[1].getRankIndex()
                or self._cards[1].getRankIndex() == self._cards[2].getRankIndex()) \
               and self._cards[0].getRankIndex() != self._cards[2].getRankIndex()

class State:
    def __init__(self, num_players):
        self.num_players = num_players
        self._poker = Poker()
        self._lenPlayer = num_players
        self._pairs = []
        self._liveState = [True] * self._lenPlayer
        self._flopState = [False] * self._lenPlayer
        self._chipPool = 0
        self._baseChip = 1
        self.turn = 0
        self.terminal = False
        self.max_chip = 100 * num_players
        self.history = []
        self._players = [Player(str(i)) for i in range(num_players)]
        [player.enterGame(self, index) for index, player in enumerate(self._players)]

    def __copy__(self):
        new_state = State(self.num_players)
        new_state._liveState = deepcopy(self._liveState)
        new_state._flopState = deepcopy(self._flopState)
        new_state.turn = self.turn
        new_state.terminal = self.terminal
        new_state._pairs = self._pairs
        new_state._chipPool = self._chipPool
        new_state._baseChip = self._baseChip
        new_state._players = deepcopy(self._players)
        new_state.history = deepcopy(self.history)
        [player.enterGame(new_state, index) for index, player in enumerate(new_state._players)]
        return new_state

    def clusterClass(self,handPairs):
        return handPairs.getClusterClass()

    def info_set(self):
        # handcards = str(self._pairs[self.turn])
        isflop = self._flopState[self.turn]
        islive = self._liveState[self.turn]
        try:
            assert islive == True
        except:
            print('?')
        group_history = []
        startIndex = 0
        sub_group = []
        for index,action in enumerate(self.history):
            sub_group.append(action)
            if not action == 'F':
                startIndex += 1
            if startIndex % self.num_players == 0 and startIndex > 0:
                startIndex = 0
                group_history.append(sub_group)
                sub_group = []
        if len(sub_group) > 0:
            group_history.append(sub_group)

        if islive:
            if isflop:
                cluster_class = str(self.clusterClass(self._pairs[self.turn]))
                info_set = f"{cluster_class} || {group_history}"
            else:
                info_set = "unflop || " + f"{group_history}"
        return info_set

    def is_terminal(self):
        lives = sum(self._liveState)
        return lives == 1

    def utility(self):
        pot = (self.num_players)*1
        winner = self._players[self._liveState.index(True)]
        # print('winner is ' + winner.getName())
        winner.winGame(self._chipPool + pot)
        payoffs = [p.payoff()-1 for p in self._players]
        return np.array(payoffs)

    def valid_actions(self):
        isflop = self._flopState[self.turn]
        actions_s = []
        for i in range(self.num_players):
            if not i == self.turn:
                islive = self._liveState[i]
                if islive:
                    actions_s.append("S"+str(i))
        actions_r = []
        if self._chipPool <= self.max_chip:
            actions_r = ["C"]
            if self._baseChip == 1:
                actions_r += ["R2","R5","R10"]
            elif self._baseChip == 2:
                actions_r += ["R5","R10"]
            elif self._baseChip == 5:
                actions_r += ["R10"]
        else:
            print(self._chipPool)
        if isflop:
            return actions_s + actions_r + ["Q"]
        return actions_s + actions_r + ["F","Q"]

    def take(self, action, deep=False):
        if deep is True:
            new_state = copy(self)
        else:
            new_state = self
        player = new_state._players[new_state.turn]
        if action == "C":
            player.call()
        if action.startswith("R"):
            index = int(action[1:])
            player.Raise(index)
        elif action == "Q":
            player.quit()
        elif action == "F":
            player.flop()
        if action.startswith("S"):
            index = int(action[1:])
            player.Solo(index)
            if new_state._liveState[player._currentIndex] == False:
                action += "_F"
        new_state.history.append(action)
        if not action == "F":
            new_state.terminal = new_state.is_terminal()
            new_state.turn = (new_state.turn + 1) % new_state.num_players
            while new_state._liveState[new_state.turn] == False:
                new_state.history.append('skip')
                new_state.turn = (new_state.turn + 1) % new_state.num_players

                if new_state.turn > new_state.num_players-1 or not len(new_state._liveState) == new_state.num_players:
                    print("error")

        return new_state

    def shuffle(self):
        self._poker.shuffle()
        # print('shuffle')

    def getPlayerState(self):
        return self._liveState.copy()

    def licensing(self):
        self.shuffle()
        for index in range(self._lenPlayer):
            cards = [self._poker[index + i * self._lenPlayer] for i in range(3)]
            self._pairs.append(Pair(cards))


    def showPair(self, playerId,show=False):
        if show:
            print('Player ' + self._players[playerId].getName() + ' has: ', str(self._pairs[playerId]) +
                  ' Value is ' + str(self._pairs[playerId].getValue()))

    def showAllPair(self,show=False):
        [self.showPair(i,show) for i in range(self._lenPlayer)]

    def recall(self, playlerIndex):
        chip = (self._flopState[playlerIndex] + 1) * self._baseChip
        self._chipPool += chip
        return chip

    def reRaise(self, playerIndex, rate):
        self._baseChip = rate
        chip = self.recall(playerIndex)
        return chip

    def reQuit(self, playerIndex):
        self._liveState[playerIndex] = False

    def reFlop(self, playerIndex):
        self._flopState[playerIndex] = True
        return str(self._pairs[playerIndex])

    def reSolo(self,playerIndex,opponentIndex):
        self_value = self._pairs[playerIndex]._value
        opponet_value = self._pairs[opponentIndex]._value
        losser = playerIndex if self_value <= opponet_value else opponentIndex
        self._liveState[losser] = False
        chip = (self._flopState[playerIndex] + 1) * self._baseChip
        self._chipPool += chip
        return chip

    def resetGame(self):
        self._poker.reset()
        self._pairs = []
        self._chipPool = 0
        self._baseChip = 1
        self._liveState = [0] * self._lenPlayer

    def isGameEnd(self):
        return sum(self._liveState) == 1

    def endGame(self):
        winner = self._players[self._liveState.index(True)]
        # print('winner is ' + winner.getName())
        winner.winGame(self._chipPool)
        self.resetGame()

def class_test():
    card0 = Card('♥', 'J')
    card1 = Card('♥', 'K')
    card2 = Card('♦', 'Q')
    cards = [card0,card1,card2]
    p = Pair(cards)
    p.getClusterClass()
    return

if __name__ == "__main__":
    class_test()