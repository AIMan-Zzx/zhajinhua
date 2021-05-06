import copy
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
def create_dir(dir_name: str = "results") -> Path:
    """Create and get a unique dir path to save to using a timestamp."""
    time = str(datetime.datetime.now())
    for char in ":- .":
        time = time.replace(char, "_")
    path: Path = Path(f"./{dir_name}_{time}")
    path.mkdir(parents=True, exist_ok=True)
    return path

def create_realtime_dir(dir_name: str = "results") -> Path:
    """Create and get a unique dir path to save to using a timestamp."""
    path: Path = Path(f"./{dir_name}_realtime")
    path.mkdir(parents=True, exist_ok=True)
    return path

def showResult(filePath):
    with open(filePath, 'r', encoding='UTF-8') as r:
        data = json.load(r)
        subdata = data["0"]
        print(data)

if __name__ == "__main__":
    showResult("node_map.json")