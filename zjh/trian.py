import logging
from pathlib import Path
from typing import Dict

import click
import joblib
import yaml
from tools import *
import argparse
global args

from multiProcess.server import Server
from singleProcess.s_train import simple_search

log = logging.getLogger("poker_ai.ai.runner")

def init_args():
    parser = argparse.ArgumentParser(description='cfr')
    parser.add_argument("--strategy_interval",
    default=100,
    help="Update the current strategy whenever the iteration % strategy_interval == 0.",)
    parser.add_argument( "--n_iterations",
    default=20,#100000,# default=15000,
    help="The total number of iterations we should train the model for.",)
    parser.add_argument( "--lcfr_threshold",
    default=400,
    help=(
        "A threshold for linear CFR which means don't apply discounting "
        "before this iteration."
    ),)
    parser.add_argument("--discount_interval",
    default=400,
    help=(
        "Discount the current regret and strategy whenever iteration % "
        "discount_interval == 0."
    ))
    parser.add_argument("--prune_threshold",
    default=400,
    help=(
        "When a uniform random number is less than 95%, and the iteration > "
        "prune_threshold, use CFR with pruning."
    ),)
    parser.add_argument( "--c",
    default=-1000,
    help=(
        "Pruning threshold for regret, which means when we are using CFR with "
        "pruning and have a state with a regret of less than `c`, then we'll "
        "elect to not recusrively visit it and it's child nodes."
    ),)
    parser.add_argument("--n_players", default=6, help="The number of players in the game.")
    parser.add_argument("--dump_iteration",
    default=10,
    help=(
        "When the iteration % dump_iteration == 0, we will compute a new strategy "
        "and write that to the accumlated strategy, which gets normalised at a "
        "later time."
    ),)
    parser.add_argument("--sync_update_strategy",
    default=False,
    help="Do or don't synchronise update_strategy.",)
    parser.add_argument("--update_threshold",
    default=100,
    help=(
        "When the iteration is greater than update_threshold we can start "
        "updating the strategy."
    ),)
    parser.add_argument("--single_process",
    default=False,
    help="Either use or don't use multiple processes.",)
    parser.add_argument("--sync_cfr", default=False, help="Do or don't synchronuse CFR.")
    parser.add_argument( "--sync_serialise",
    default=False,
    help="Do or don't synchronise the serialisation.",)
    parser.add_argument("--sync_discount",
    default=False,
    help="Do or don't synchronise the discounting.")
    parser.add_argument("--nickname", default="", help="The nickname of the study.")
    args = parser.parse_args()
    return args

def _sub_search(server: Server):
    """Safely run the server, and allow user to control c."""
    try:
        server.sub_search()
    except (KeyboardInterrupt, SystemExit):
        log.info(
            "Early termination of program. Please wait for workers to "
            "terminate."
        )

def _safe_search(server: Server):
    """Safely run the server, and allow user to control c."""
    try:
        server.search()
    except (KeyboardInterrupt, SystemExit):
        log.info(
            "Early termination of program. Please wait for workers to "
            "terminate."
        )
    finally:
        server.terminate()
    print("All workers terminated. Quitting program - thanks for using me!")
    log.info("All workers terminated. Quitting program - thanks for using me!")



def start(
    strategy_interval: int,
    n_iterations: int,
    lcfr_threshold: int,
    discount_interval: int,
    prune_threshold: int,
    c: int,
    n_players: int,
    dump_iteration: int,
    update_threshold: int,
    single_process: bool,
    sync_update_strategy: bool,
    sync_cfr: bool,
    sync_discount: bool,
    sync_serialise: bool,
    nickname: str,
    currentstate=None,
    submap=None,
    realtime=None
):
    """Train agent from scratch."""
    # Write config to file, and create directory to save results in.
    config: Dict[str, int] = {**locals()}
    if not realtime:
        save_path: Path = create_dir(nickname)
    else:
        save_path: Path = create_realtime_dir(nickname)
    with open(save_path / "config.yaml", "w") as steam:
        yaml.dump(config, steam)
    if single_process:
        log.info(
            "Only one process specified so using poker_ai.ai.singleprocess."
            "simple_search for the optimisation."
        )
        simple_search(
            config=config,
            save_path=save_path,
            strategy_interval=strategy_interval,
            n_iterations=n_iterations,
            lcfr_threshold=lcfr_threshold,
            discount_interval=discount_interval,
            prune_threshold=prune_threshold,
            c=c,
            n_players=n_players,
            dump_iteration=dump_iteration,
            update_threshold=update_threshold,
            # node_map=node_map,
            # action_map = action_map
        )
        return None
    else:
        log.info(
            "Mulitple processes specifed so using poker_ai.ai.multiprocess."
            "server.Server for the optimisation."
        )
        map = {i: {} for i in range(n_players)}
        # Create the server that controls/coordinates the workers.
        server = Server(
            strategy_interval=strategy_interval,
            n_iterations=n_iterations,
            lcfr_threshold=lcfr_threshold,
            discount_interval=discount_interval,
            prune_threshold=prune_threshold,
            c=c,
            n_players=n_players,
            dump_iteration=dump_iteration,
            update_threshold=update_threshold,
            save_path=save_path,
            sync_update_strategy=sync_update_strategy,
            sync_cfr=sync_cfr,
            sync_discount=sync_discount,
            sync_serialise=sync_serialise,
            init_state=currentstate,
            init_map = submap,
            realtime=realtime
        )
        if realtime:
            _sub_search(server)
        else:
            _safe_search(server)

def subgame(cur_state=None,is_realtime=False):
    args = init_args()
    start(
        args.strategy_interval,
        args.n_iterations,
        args.lcfr_threshold,
        args.discount_interval,
        args.prune_threshold,
        args.c,
        args.n_players,
        args.dump_iteration,
        args.update_threshold,
        args.single_process,
        args.sync_update_strategy,
        args.sync_cfr,
        args.sync_discount,
        args.sync_serialise,
        args.nickname,
        currentstate=cur_state,
        submap=None,
        realtime=is_realtime,
    )


if __name__ == "__main__":
    subgame()