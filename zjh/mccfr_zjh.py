import numpy as np
import random
from itertools import permutations
from tqdm import tqdm
from typing import Dict, List, Union
import multiprocessing as mp
from collections import defaultdict
from node import MNode as Node
from state import State,Pair
import json
import sys
import os
sys.setrecursionlimit(1000000)
# regret_minimum = -300000
regret_minimum = -100
prune_threshold = 200

def new_game(num_players):
    state = State(num_players)
    state.licensing()
    state.showAllPair()
    return state

def sub_train(t,state,node_map,locks = {},alpha=1):
    for player in range(state.num_players):
        if t > prune_threshold:
            chance = np.random.rand()
            if chance < .05:
                mccfr(player, state, node_map, locks,alpha=alpha)
            else:
                mccfr(player, state, node_map, locks, prune=True,alpha=alpha)
        else:
            mccfr(player, state, node_map, locks,alpha=alpha)

def train(iterations,num_players, node_map,locks = {}):#locks: Dict[str, mp.synchronize.Lock] = {}):
    for t in tqdm(range(1, iterations + 1), desc='Training'):
        state = new_game(num_players)
        for player in range(num_players):
            if t > prune_threshold:
                chance = np.random.rand()
                if chance < .05:
                    mccfr(player, state, node_map,locks)
                else:
                    mccfr(player, state, node_map,locks, prune=True)
            else:
                mccfr(player, state, node_map,locks)

def mccfr(traverser, state, node_map,locks = {},alpha=1, prune=False):#locks: Dict[str, mp.synchronize.Lock] = {}, prune=False):
    turn = state.turn
    num_players = state.num_players
    player_not_in_hand = not state._liveState[traverser]
    if state.terminal:
        utility = state.utility()
        return utility
    elif player_not_in_hand:
        payoffs = [0 for _ in range(num_players)]
        for index,player in enumerate(state._players):
            islive = state._liveState[index]
            player = state._players[index]
            payoffs[index] = 0 if islive else player.payoff() - 1
        return np.array(payoffs)
    elif turn == traverser:
        info_set = state.info_set()
        valid_actions = state.valid_actions()
        node = node_map[state.turn].get(info_set, Node(valid_actions))
        strategy = node.strategy()

        node_util = np.zeros(len(node_map))
        util = {action: 0 for action in valid_actions}
        explored = set(valid_actions)

        for action in valid_actions:
            if prune is True and node.regret_sum[action] <= regret_minimum:
                # if node.regret_sum[action] < 0:
                explored.remove(action)
            else:
                if action not in strategy:
                    explored.remove(action)
                    continue
                new_state = state.take(action,deep=True)
                returned = mccfr(traverser, new_state, node_map,
                                 locks,alpha,prune=prune)

                util[action] = returned[turn]
                node_util += returned * strategy[action]
        if locks:
            locks["regret"].acquire()
        for action in explored:
            regret = util[action] - node_util[turn]
            node.regret_sum[action] += regret * alpha
            node_map[state.turn][info_set] = node
        if locks:
            locks["regret"].release()
        return node_util

    else:
        info_set = state.info_set()
        valid_actions = state.valid_actions()
        node = node_map[state.turn].get(info_set, Node(valid_actions))
        strategy = node.strategy()

        actions = list(strategy.keys())
        prob = list(strategy.values())
        random_action = random.choices(actions, weights=prob)[0]
        new_state = state.take(random_action,deep=True)
        return mccfr(traverser, new_state, node_map, locks,alpha,prune=prune)

def serialise(node_map,save_path,name="single",locks = {}):
    if locks:
        locks["regret"].acquire()
    filepath = os.path.abspath(("{}/{}_node_map.json").format(save_path,name))
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='UTF-8') as r:
            jsonfile = json.load(r)
        for key, value in node_map.items():
            values = []
            valueDict = {}

            exsit_values = jsonfile[str(key)]
            for sub_key, sub_value in value.items():
                if sub_key in exsit_values:
                    exsit_regret_sum = exsit_values[sub_key]
                    addresult = []
                    for acton,prob in sub_value.regret_sum.items():
                        addresult.append({acton:(float(prob)+exsit_regret_sum["regret_sum"][acton])})

                    valueDict[sub_key] = {'regret_sum': addresult}
                else:
                    valueDict[sub_key] = {'regret_sum': sub_value.regret_sum}
            jsonfile[key] = valueDict

    else:
        jsonfile = {}
        for key, value in node_map.items():
            values = []
            valueDict = {}
            for sub_key, sub_value in value.items():
                valueDict[sub_key] = {'regret_sum': sub_value.regret_sum}
            jsonfile[key] = valueDict
        with open(filepath, 'w', encoding='UTF-8') as w:
            file = json.dumps(jsonfile)
            w.write(file)
    if locks:
        locks["regret"].release()

def subgame_slover(state,iter_num=100):
    n_players = state.num_players
    node_map = {i: {} for i in range(n_players)}
    for t in tqdm(range(1, iter_num + 1), desc='Training'):
        for i in range(n_players):
            if state._liveState[i] and state._flopState[i]:
                state.shuffle()
                state._pairs[i] = Pair(state._poker[:3])

        for player in range(n_players):
            if t > prune_threshold:
                chance = np.random.rand()
                if chance < .05:
                    mccfr(player, state, node_map)
                else:
                    mccfr(player, state, node_map, prune=True)
            else:
                mccfr(player, state, node_map)
    return node_map

