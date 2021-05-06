from state import State
import json
from mccfr_zjh import *
import random
from copy import copy, deepcopy
from trian import subgame



n_players = 6
state = new_game(n_players)
realtime_node_path = "_realtime/muti_node_map.json"



node_path = "test_node_map.json"
with open(node_path, 'r', encoding='UTF-8') as r:
    data = json.load(r)
strangys = [data[str(i)] for i in range(n_players)]


def c_strategy(regret_sum):
    strat = {action: max(value, 0) for action, value in
             regret_sum.items()}

    norm_sum = sum([strat[key] for key in strat])
    actions = regret_sum.keys()
    if norm_sum > 0:
        strat = {key: strat[key] / norm_sum for key in actions}
    else:
        num_valid = len(actions)
        strat = {key: 1 / num_valid for key, value in strat.items()}

    return strat

while not state.terminal:
    turn = state.turn
    print('turn == {}'.format(turn))
    strangy = strangys[turn]
    info_set = state.info_set()
    print("info_set: {}".format(info_set))
    valid_actions = state.valid_actions()
    if info_set not in strangy:
        print('subgame')
        new_state = copy(state)
        try:
            data = subgame_slover(new_state,100)
            # subgame(new_state,is_realtime=True)
        finally:
            # with open(realtime_node_path, 'r', encoding='UTF-8') as r:
            #     data = json.load(r)
            # print(data)
            # node = data[str(turn)][info_set]
            # strategy = c_strategy(node["regret_sum"])

            node = data[turn][info_set]
            strategy = node.regret_sum
            actions = list(strategy.keys())
            print("actions 》》》 " + " ".join(actions))
            prob = list(strategy.values())
            random_action = random.choices(actions, weights=prob)[0]
            print("choose action: {}".format(random_action))
            state.take(random_action, deep=False)
    else:
        node = strangy[info_set]
        strategy = node["regret_sum"]
        actions = list(strategy.keys())
        print("actions 》》》 " + " ".join(actions))

        strat = c_strategy(strategy)
        prob = list(strat.values())
        random_action = random.choices(actions, weights=prob)[0]
        print("choose action: {}".format(random_action))
        state.take(random_action, deep=False)
else:
    winner = state._liveState.index(True)
    state.showAllPair(show=True)
    state.showPair(winner,show=True)
