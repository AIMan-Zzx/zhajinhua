import os
import sys
sys.path.insert(0, os.path.abspath("../"))
import random
from pathlib import Path
from typing import Dict
from tqdm import tqdm, trange
import numpy as np
import random

from mccfr_zjh import *

def print_strategy(strategy: Dict[str, Dict[str, int]]):
    """
    Print strategy.

    ...

    Parameters
    ----------
    strategy : Dict[str, Dict[str, int]]
        The preflop strategy for our agent.
    """
    for info_set, action_to_probabilities in sorted(strategy.items()):
        norm = sum(list(action_to_probabilities.values()))
        tqdm.write(f"{info_set}")
        for action, probability in action_to_probabilities.items():
            tqdm.write(f"  - {action}: {probability / norm:.2f}")

def simple_search(
    config: Dict[str, int],
    save_path: Path,
    strategy_interval: int,
    n_iterations: int,
    lcfr_threshold: int,
    discount_interval: int,
    prune_threshold: int,
    c: int,
    n_players: int,
    dump_iteration: int,
    update_threshold: int,
):
    """
    Train agent.

    ...

    Parameters
    ----------
    config : Dict[str, int],
        Configurations for the simple search.
    save_path : str
        Path to save to.
    strategy_interval : int
        Iteration at which to update strategy.
    n_iterations : int
        Number of iterations.
    lcfr_threshold : int
        Iteration at which to begin linear CFR.
    discount_interval : int
        Iteration at which to discount strategy and regret.
    prune_threshold : int
        Iteration at which to begin pruning.
    c : int
        Floor for regret at which we do not search a node.
    n_players : int
        Number of players.
    dump_iteration : int
        Iteration at which we begin serialization.
    update_threshold : int
        Iteration at which we begin updating strategy.
    """
    node_map = {i: {} for i in range(n_players)}

    np.random.seed(42)
    random.seed(42)
    for t in trange(1, n_iterations + 1, desc="train iter"):
        alpha = min((t/n_iterations) * 1000,1)
        for i in range(n_players):  # fixed position i
            # Create a new state.
            state = new_game(n_players)
            if t > update_threshold and t % strategy_interval == 0:
                pass#update_strategy(i, state, node_map, action_map)
            if t > prune_threshold:
                if random.uniform(0, 1) < 0.05:
                    mccfr(i, state, node_map,alpha=alpha, prune=False)
                else:
                    mccfr(i, state, node_map,alpha=alpha, prune=True)
            else:
                mccfr(i, state, node_map,alpha=alpha, prune=False)
        if t < lcfr_threshold & t % discount_interval == 0:
            pass
        if (t > update_threshold) & (t % dump_iteration == 0):
            # dump the current strategy (sigma) throughout training and then
            # take an average. This allows for estimation of expected value in
            # leaf nodes later on using modified versions of the blueprint
            # strategy.
            pass#serialise(node_map, save_path)
    serialise(node_map,save_path)