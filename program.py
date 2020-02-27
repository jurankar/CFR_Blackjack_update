from random import random as randDec
import random
import numpy as np

class node:
    NUM_ACTIONS = 3

    def __init__(self):
        self.infoSet = ""
        self.regretSum = np.zeros((self.NUM_ACTIONS))
        self.strategy = np.zeros((self.NUM_ACTIONS))   # verjetnost da zberemo HIT, STAND, DOUBLE
        self.strategySum = np.zeros((self.NUM_ACTIONS)) # --> 0=Hit 1=Stand 2=Double
        self.avgStrat = []              # --> to be optimized !

    #strategy[] je ubistvu sam normaliziran regretSum[] --> skor copy paste iz RM rock paper scissors
    def getStrat(self, realizationWeight):

        # if(not (self.regretSum[0] == 0 and self.regretSum[1] == 0) ):    # if da ne gre pr prvi iteraciji notr
        normalizingSum = 0

        for i in range(self.NUM_ACTIONS):
            self.strategy[i] = self.regretSum[i] if self.regretSum[i] > 0 else 0
            normalizingSum += self.strategy[i]

        for i in range(self.NUM_ACTIONS):
            if(normalizingSum > 0):
                self.strategy[i] /= normalizingSum
            else:
                self.strategy[i] = 1.0 / self.NUM_ACTIONS
            self.strategySum[i] += realizationWeight * self.strategy[i]

        #debugging
        self.avgStrat = self.getAvgStrat()

        return self.strategy


    # vzamemo povprečno strategijo ki jo mamo v stretegySum[] od prej
    # ker vsaka posamična strategija je lahko negativna
    # ubistvu sam normaliziramo strategySum[]
    def getAvgStrat(self):  # --> cisti copy paste iz RM rock paper scissors
        avgStrat = np.zeros((self.NUM_ACTIONS))
        normalizingSum = 0
        for i in range(self.NUM_ACTIONS):
            normalizingSum += self.strategySum[i]
        for i in range(self.NUM_ACTIONS):
            if(normalizingSum > 0):
                avgStrat[i] = self.strategySum[i] / normalizingSum
            else:
                # print("i feel blue")
                avgStrat[i] = 1.0 / self.NUM_ACTIONS
        return avgStrat

    def toString(self):
        return ((self.infoSet),":   ",self.getAvgStrat())

# --------------------------------------------------------------------------------------------------



class Kuhn_Poker_Learner:
    PASS = 0
    BET = 1
    NUM_ACTIONS = 3
    nodeMap = {}    # ta dictionary povezuje infoSete z nodi


    def convertHistory(self, history):

        splitHis = history.split('|')

        dealerCards = splitHis[0]
        playerCards = splitHis[1].split(',')
        for ind, card in enumerate(playerCards):       # !! mogoce ne spreminja dejanske tabele
            playerCards[ind] = card[1:]

        return playerCards, dealerCards

    def sumCards(self, cards, avalibleAces):
        count = sum(cards)
        if count > 21:  # --> ce je cez 21 pogledamo ce je notr as
            if avalibleAces > 0:   # !! loh da je 11 ne "11"
                count -= 10
                avalibleAces -= 1

        return count, avalibleAces

    def payoff(self, cards, cardIndex, roundNum, history, stava, avalibleAcesPl, avalibleAcesDe):

        playerCards, dealerCards = self.convertHistory(history)
        if isinstance(dealerCards, (str)):
            dealerCards = [dealerCards]
        if(playerCards[ len(playerCards) - 1] == '' ):
            playerCards.pop(len(playerCards) - 1)

        playerCount, avalibleAcesPl = self.sumCards(playerCards, avalibleAcesPl)
        dealerCount, avalibleAcesDe = self.sumCards(dealerCards, avalibleAcesDe)


        if roundNum == 1:
            if playerCount > 21:
                return -stava
            elif playerCount == 21:
                return  1.5 * stava
            else:
                return "continue"

        elif roundNum == 2:
            while True:
                if dealerCount > 21:
                    return stava
                elif dealerCount < 17:
                    dealerCards.append(cards[cardIndex])
                    dealerCount, avalibleAcesDe = self.sumCards(cards, avalibleAcesDe)
                    cardIndex += 1

                else:
                    if playerCount > dealerCount: return stava
                    elif playerCount < dealerCount: return -stava
                    elif playerCount == dealerCount: return 0
                    else:
                        return "error line cca 108"
        else:
            return "error line cca 110"


    def cfr(self, cards, history, p0, stava, cardsIndex, avalibleAcesPl, avalibleAcesDe):
        """
        history bo v obliki :"DealerCount|PlayerCount" --> "9|18"  ali ko damo stand "8|19S|"
        """


        if history == "":
            history = str(cards[0]) + "|" + str(cards[1])
            if(cards[0] == 11):
                avalibleAcesDe += 1
            if(cards[1] == 11):
                avalibleAcesPl += 1
            cardsIndex += 2 # cardsIndex = 2

        roundNum = history.count('|')  # --> kje v igri smo

        # dobimo payoff ce je končno stanje
        payoff = self.payoff(cards, cardsIndex,roundNum, history, stava, usedAcesPl, usedAcesDe)
        if payoff != "continue":
            return payoff

        # dobimo v katerem stanju/nodu/situaciji trenutno smo
        infoSet = history
        if infoSet in self.nodeMap:
            newNode1 = self.nodeMap[infoSet]
        else:
            newNode1 = node()   # --> ko se node kreira se ze skopirajo ostale vrednosti iz drugih nodov...ne gre iz nule
            newNode1.infoSet = infoSet
            self.nodeMap[infoSet] = newNode1


        # rekurzivno kličemo self.cfr za opcijo bet in opcijo pass
        strategy = newNode1.getStrat(p0)
        util = np.zeros((self.NUM_ACTIONS))   # kolk utila mamo za bet pa kolk za pass
        nodeUtil = 0


        playerCount, dealerCount = self.convertHistory(history)
        playerCount = playerCount + cards[cardsIndex]
        if cards[cardsIndex] == 11:
            avalibleAcesPl += 1
        cardsIndex += 1
        newHistory = str(dealerCount) + "|" + str(playerCount)

        for i in range(self.NUM_ACTIONS):   # --> 0=Hit 1=Stand 2=Double

            if i == 0:
                nextHistory = newHistory
                util[i] =  self.cfr(cards, nextHistory, p0 * strategy[i], stava, cardsIndex + 1, avalibleAcesPl, avalibleAcesDe)             # --> tuki poprau da prvo prever ce lahko sploh stau
            elif i == 1:
                nextHistory = history + "S|"
                util[i] =  self.cfr(cards, nextHistory, p0 * strategy[i], stava, cardsIndex + 1, avalibleAcesPl, avalibleAcesDe)
            if i == 2:
                nextHistory = newHistory
                util[i] =  self.cfr(cards, nextHistory, p0 * strategy[i], stava * 2, cardsIndex + 1, avalibleAcesPl, avalibleAcesDe)

            nodeUtil += strategy[i] * util[i]

        # zdj pa seštejemo counter factual regret
        for i in range(self.NUM_ACTIONS):
            regret = util[i] - nodeUtil
            newNode1.regretSum[i] += p0 * regret

        return nodeUtil


    def train(self, stIteracij):
        cards = [2,2,2,2, 3,3,3,3, 4,4,4,4, 5,5,5,5, 6,6,6,6, 7,7,7,7, 8,8,8,8, 9,9,9,9, 10,10,10,10, 10,10,10,10, 10,10,10,10, 10,10,10,10, 11,11,11,11]
        game_return = 0

        for i in range(stIteracij):

            if i % (stIteracij/100) == 0:
                print(i / (stIteracij/100), " %")

            random.shuffle(cards)
            game_return += self.cfr(cards, "", 1, 1, 0, 0, 0)

        # print("Average game return: ", util / stIteracij)
        return self.nodeMap


# --------------------------------------------------------------------------------------------------



def stevilkaVKarto(st):

    switcher = {
        1: "2",
        2: "3",
        3: "4",
        4: "5",
        5: "6",
        6: "7",
        7: "8",
        8: "9",
        9: "10",
        10: "J",
        11: "Q",
        12: "K",
        13: "A"
    }

    return (switcher.get(st, "Error ni te karte"))








if __name__ == "__main__":
    learner = Kuhn_Poker_Learner()
    mapaNodov = learner.train(1000000)

    # igranje igre
    # igrajIgro(mapaNodov)


