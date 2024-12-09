import os
import signal
import multiprocessing
from queue import Empty

class TimeoutError(Exception):
    pass

def run_with_timeout(func, seconds, *args, **kwargs):
    """
    Run a function with a timeout limit.
    
    Args:
        func: The function to run
        seconds: Number of seconds before timeout
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function if it completes within the timeout
        
    Raises:
        TimeoutError: If the function doesn't complete within the specified time
        Any exception that the function itself raises
    """
    result_queue = multiprocessing.Queue()
    
    def worker(queue):
        try:
            os.setpgrp()
            result = func(*args, **kwargs)
            queue.put(result)
        except Exception as e:
            queue.put(e)

    process = multiprocessing.Process(target=worker, args=(result_queue,))
    process.start()
    
    try:
        result = result_queue.get(timeout=seconds)
        
        if isinstance(result, Exception):
            raise result
            
        return result
    except Empty:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except:
            pass
        raise TimeoutError(f"Function timed out after {seconds} seconds")
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=0.1)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except:
                pass
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except:
                pass