import os
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent

def get_package_root() -> Path:
    return Path(__file__).parent.parent

def get_results_dir() -> str:
    return os.path.join(get_project_root(), "results")

def get_logs_dir() -> str:
    return os.path.join(get_project_root(), "logs")

def get_networks_dir() -> str:
    return os.path.join(get_project_root(), "networks")

def _check_if_external_epanet_inp_file(epanet_network: str) -> bool:
    sep = os.path.sep
    return sep in epanet_network

DEFAULT_SANDBOX_NETWORK_LOCATION = "/sandbox/network.inp"