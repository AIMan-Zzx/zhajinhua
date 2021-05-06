import logging
import multiprocessing as mp
import os
import time
from pathlib import Path
from typing import Dict, Optional, Union

import enlighten

from glob import glob
import os
import sys
sys.path.insert(0, os.path.abspath("../"))
from mccfr_zjh import *
from multiProcess.worker import Worker

log = logging.getLogger("sync.server")
manager = mp.Manager()


class Server:
    """Server class to manage all workers optimising CFR algorithm."""

    def __init__(
        self,
        strategy_interval: int,
        n_iterations: int,
        lcfr_threshold: int,
        discount_interval: int,
        prune_threshold: int,
        c: int,
        n_players: int,
        dump_iteration: int,
        update_threshold: int,
        save_path: Union[str, Path],
        sync_update_strategy: bool = False,
        sync_cfr: bool = False,
        sync_discount: bool = False,
        sync_serialise: bool = False,
        start_timestep: int = 1,
        n_processes: int = 5,# n_processes: int = mp.cpu_count() - 1,
        init_state = None,
        init_map=None,
        realtime=False
    ):
        """Set up the optimisation server."""
        if init_map == None:
            self.node_map = {i: {} for i in range(n_players)}
        else:
            self.node_map = init_map
        self._strategy_interval = strategy_interval
        self._n_iterations = n_iterations
        self._lcfr_threshold = lcfr_threshold
        self._discount_interval = discount_interval
        self._prune_threshold = prune_threshold
        self._c = c
        self._n_players = n_players
        self._dump_iteration = dump_iteration
        self._update_threshold = update_threshold
        self._save_path = save_path
        self._sync_update_strategy = sync_update_strategy
        self._sync_cfr = sync_cfr
        self._sync_discount = sync_discount
        self._sync_serialise = sync_serialise
        self._start_timestep = start_timestep
        log.info("Loaded lookup table.")
        self._job_queue: mp.JoinableQueue = mp.JoinableQueue(maxsize=n_processes)
        self._status_queue: mp.Queue = mp.Queue()
        self._logging_queue: mp.Queue = mp.Queue()
        self._worker_status: Dict[str, str] = dict()
        self._locks: Dict[str, mp.synchronize.Lock] = dict(
            regret=mp.Lock(), strategy=mp.Lock()
        )
        self.subgame = realtime
        self._state = init_state
        if os.environ.get("TESTING_SUITE"):
            n_processes = 4
        self._workers: Dict[str, Worker] = self._start_workers(n_processes,self._state)

    def sub_search(self):
        """Perform MCCFR and train the agent.

        If all `sync_*` parameters are set to True then there shouldn't be any
        difference between this and the original MCCFR implementation.
        """
        progress_bar_manager = enlighten.get_manager()
        progress_bar = progress_bar_manager.counter(
            total=self._n_iterations, desc="Optimisation iterations", unit="iter"
        )
        for t in range(self._start_timestep, self._n_iterations + 1):
            # Log any messages from the worker in this master process to avoid
            # weirdness with tqdm.
            alpha = min((t / self._n_iterations) * 1000, 1)
            print('>>>>iter {}<<<<'.format(t))
            while not self._logging_queue.empty():
                log.info(self._logging_queue.get())
            # Optimise for each player's position.
            self.job("sub_train", sync_workers=self._sync_cfr, t=t,alpha=alpha)
            progress_bar.update()
        self.serialise()

    def search(self):
        """Perform MCCFR and train the agent.

        If all `sync_*` parameters are set to True then there shouldn't be any
        difference between this and the original MCCFR implementation.
        """
        log.info(f"synchronising update_strategy - {self._sync_update_strategy}")
        log.info(f"synchronising cfr             - {self._sync_cfr}")
        log.info(f"synchronising discount        - {self._sync_discount}")
        log.info(f"synchronising serialise_agent - {self._sync_serialise}")
        progress_bar_manager = enlighten.get_manager()
        progress_bar = progress_bar_manager.counter(
            total=self._n_iterations, desc="Optimisation iterations", unit="iter"
        )

        for t in range(self._start_timestep, self._n_iterations + 1):
            # Log any messages from the worker in this master process to avoid
            # weirdness with tqdm.
            alpha = min((t / self._n_iterations) * 1000, 1)

            print('>>>>iter {}<<<<'.format(t))
            while not self._logging_queue.empty():
                log.info(self._logging_queue.get())
            # Optimise for each player's position.
            for i in range(self._n_players):
                self.job("cfr", sync_workers=self._sync_cfr, t=t, i=i,alpha=alpha)
            progress_bar.update()
        self.serialise()

    def serialise(self):
        self._wait_until_all_workers_are_idle()
        for i in range(len(self._workers)):
            # name = "Worker-{}".format(i+2)
            # woker = self._workers[name]
            # print(woker.name,woker.node_map)
            self.job(
                    "serialise",
                    sync_workers=self._sync_serialise,
                )
        self._job_queue.join()
        self.comb_node()
        self._wait_until_all_workers_are_idle()

    def save_sub(self, filepath,save_path,name="muti", locks={}):
        mutipath = os.path.abspath(("{}/{}_node_map.json").format(save_path, name))
        # filepath = os.path.abspath(str(save_path / f"node_map.json"))
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='UTF-8') as r:
                jsonfile = json.load(r)
        if os.path.isfile(mutipath):
            with open(mutipath, 'r', encoding='UTF-8') as mr:
                saved_file = json.load(mr)
                for idkey, value in jsonfile.items():
                    values = []
                    valueDict = {}
                    exsit_values = saved_file[str(idkey)]
                    for info_key, sub_value in value.items():
                        if info_key in exsit_values:
                            exsit_regret_sum = exsit_values[info_key]
                            addresult = {}
                            for action, prob in sub_value["regret_sum"].items():
                                addresult[action] = float(prob) + exsit_regret_sum["regret_sum"][action]

                            valueDict[info_key] = {'regret_sum': addresult}
                        else:
                            valueDict[info_key] = {'regret_sum': sub_value["regret_sum"]}
                    jsonfile[idkey] = valueDict

                for idkey, value in saved_file.items():
                    values = []
                    valueDict = {}
                    exsit_values = jsonfile[str(idkey)]
                    for info_key, sub_value in value.items():
                        if not info_key in exsit_values:
                            exsit_values[info_key] = sub_value
                    jsonfile[idkey] = exsit_values


        with open(mutipath, 'w', encoding='UTF-8') as w:
            file = json.dumps(jsonfile)
            w.write(file)


    def get_file_list(self,folder_path, sub_dir: bool = True) -> list:
        """
        获取所给文件目录里的指定后缀的文件,读取文件列表目前使用的是 os.walk 和 os.listdir ，这两个目前比 pathlib 快很多
        :param filder_path: 文件夹名称
        :param p_postfix: 文件后缀,如果为 [.*]将返回全部文件
        :param sub_dir: 是否搜索子文件夹
        :return: 获取到的指定类型的文件列表
        """
        assert os.path.exists(folder_path) and os.path.isdir(folder_path)
        path = "/home/zzx/zjh/"+ str(folder_path) + "/"
        file_list = glob(path + "*.json")
        return file_list

    def comb_node(self):
        for json_path in self.get_file_list(self._save_path):

            self.save_sub(json_path,self._save_path)

    def terminate(self, safe: bool = False):
        """Kill all workers."""
        print("terminate")
        if safe:
            # Wait for all workers to finish their current jobs.
            self._job_queue.join()
            # Ensure all workers are idle.
            self._wait_until_all_workers_are_idle()
        # Send the terminate command to all workers.
        for _ in self._workers.values():
            name = "terminate"
            kwargs = dict()
            self._job_queue.put((name, kwargs), block=True)
            log.info("sending sentinel to worker")
        for name, worker in self._workers.items():
            worker.join()
            log.info(f"worker {name} joined.")

    def job(self, job_name: str, sync_workers: bool = False, **kwargs):
        """
        Create a job for the workers.

        ...

        Parameters
        ----------
        job_name : str
            Name of job.
        sync_wrokers : bool
            Whether or not to synchronize workers.
        """
        func = self._syncronised_job if sync_workers else self._send_job
        func(job_name, **kwargs)

    def _send_job(self, job_name: str, **kwargs):
        """Send job of type `name` with arguments `kwargs` to worker pool."""
        self._job_queue.put((job_name, kwargs), block=True)

    def _syncronised_job(self, job_name: str, **kwargs):
        """Only perform this job with one process."""
        # Wait for all enqueued jobs to be completed.
        self._job_queue.join()
        # Wait for all workers to become idle.
        self._wait_until_all_workers_are_idle()
        log.info(f"Sending synchronised {job_name} to workers")
        log.info(self._worker_status)
        # Send the job to a single worker.
        self._send_job(job_name, **kwargs)
        # Wait for the synchronised job to be completed.
        self._job_queue.join()
        # The status update of the worker starting the job should be flushed
        # first.
        name_a, status = self._status_queue.get(block=True)
        assert status == job_name, f"expected {job_name} but got {status}"
        # Next get the status update of the job being completed.
        name_b, status = self._status_queue.get(block=True)
        assert status == "idle", f"status should be idle but was {status}"
        assert name_a == name_b, f"{name_a} != {name_b}"

    def _start_workers(self, n_processes: int,init_state) -> Dict[str, Worker]:
        """Begin the processes."""
        workers = dict()
        for _ in range(n_processes):
            worker = Worker(
                job_queue=self._job_queue,
                status_queue=self._status_queue,
                logging_queue=self._logging_queue,
                locks=self._locks,
                n_players=self._n_players,
                prune_threshold=self._prune_threshold,
                c=self._c,
                lcfr_threshold=self._lcfr_threshold,
                discount_interval=self._discount_interval,
                update_threshold=self._update_threshold,
                dump_iteration=self._dump_iteration,
                save_path=self._save_path,
                node_map=self.node_map,
                subgame=self.subgame,
                cstate = init_state,
            )
            workers[worker.name] = worker
        for name, worker in workers.items():
            worker.start()
            log.info(f"started worker {name}")
        return workers

    def _wait_until_all_workers_are_idle(self, sleep_secs=0.5):
        """Blocks until all workers have finished their current job."""
        while True:
            # Read all status updates.
            while not self._status_queue.empty():
                worker_name, status = self._status_queue.get(block=False)
                self._worker_status[worker_name] = status
            # Are all workers idle, all workers statues obtained, if so, stop
            # waiting.
            all_idle = all(status == "idle" for status in self._worker_status.values())
            all_statuses_obtained = len(self._worker_status) == len(self._workers)
            if all_idle and all_statuses_obtained:
                break
            time.sleep(sleep_secs)
            log.info({w: s for w, s in self._worker_status.items() if s != "idle"})
