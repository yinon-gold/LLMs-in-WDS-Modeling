from typing import Tuple
import subprocess
import sys
from llm_sandbox import SandboxSession
from llm_epanet.utils.logger import logger
from llm_epanet.utils.utils import DEFAULT_SANDBOX_NETWORK_LOCATION, _check_if_external_epanet_inp_file


def execute_code_fast(code: str, timeout: int = 5) -> Tuple[str, str]:
    try:
        python_exec_path = sys.executable
        res = subprocess.run(
            [python_exec_path, '-c', code],
            check=True,
            capture_output=True,
            timeout=timeout
        )
        stdout = res.stdout.decode('utf-8').strip().split('\n')[-1]
        return stdout, None
    except subprocess.TimeoutExpired as e:
        logger.error(f"Code execution timed out after {timeout} seconds")
        return None, str(e)
    except subprocess.CalledProcessError as e:
        logger.error(f"Code execution failed with return code {e.returncode}")
        return None, e.stderr.decode('utf-8') if e.stderr else str(e)
    except Exception as e:
        logger.error(f"Unexpected error during code execution: {str(e)}")
        return None, str(e)


def execute_code_sandbox(code: str, timeout: int = 60, **kwargs) -> Tuple[str, str]:
    with SandboxSession(lang="python") as session:
        if 'epanet_network' in kwargs and _check_if_external_epanet_inp_file(kwargs['epanet_network']):
            network_path = kwargs['epanet_network']
            session.copy_to_runtime(src=network_path, dest=DEFAULT_SANDBOX_NETWORK_LOCATION)
        
        result = session.run(code, libraries=["numpy", "epyt"], timeout=timeout)
        
        # workaround for sandbox stdout/stderr mixup in case of UserWarning from epyt
        # Extract the actual result (last line) even when UserWarning is present
        if 'UserWarning' in result.stdout:
            logger.debug(f"Executed code in sandbox environment with UserWarning")
            # Get the last line which should contain the actual result
            actual_result = result.stdout.strip().split('\n')[-1]
        else:
            actual_result = result.stdout.strip()

        logger.info(f"Executed code in sandbox environment:\n{code}")
        logger.info(f"Execution complete; STDOUT: {actual_result}, STDERR: {result.stderr.strip()}")
    return actual_result, result.stderr.strip()

def execute_code_util(code: str, fast_mode: bool = True, timeout: int = 5, **kwargs) -> Tuple[str, str]:
    if fast_mode:
        return execute_code_fast(code, timeout=timeout)
    else:
        return execute_code_sandbox(code, timeout=timeout, **kwargs)    

