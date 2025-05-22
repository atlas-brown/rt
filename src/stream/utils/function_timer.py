import time
import functools
from typing import Dict, Any, Callable, TypeVar, List, Optional, Tuple, cast, Type

# Function type variable for generic typing
F = TypeVar('F', bound=Callable[..., Any])

class FunctionTimerRegistry:
    """Registry for storing timing information for decorated functions."""
    
    _function_stats: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register_call(cls, module_name: str, func_name: str, execution_time: float) -> None:
        """Register a function call with its execution time."""
        if module_name not in cls._function_stats:
            cls._function_stats[module_name] = {}
            
        if func_name not in cls._function_stats[module_name]:
            cls._function_stats[module_name][func_name] = {
                'total_time': 0.0,
                'calls': 0,
                'avg_time': 0.0
            }
        
        stats = cls._function_stats[module_name][func_name]
        stats['total_time'] += execution_time
        stats['calls'] += 1
        stats['avg_time'] = stats['total_time'] / stats['calls']
    
    @classmethod
    def get_stats(cls) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all collected function statistics."""
        return cls._function_stats
    
    @classmethod
    def print_stats(cls) -> None:
        """Print all collected function statistics in a formatted way."""
        print("\n=== Function Execution Statistics ===")
        
        # Calculate column widths for clean formatting
        module_width = max([len(module) for module in cls._function_stats.keys()], default=10)
        func_width = max([len(func) for module in cls._function_stats.values() 
                          for func in module.keys()], default=20)
        
        # Print header
        header = f"{'Module':<{module_width}} | {'Function':<{func_width}} | {'Calls':>8} | {'Total Time (s)':>15} | {'Avg Time (s)':>15}"
        print(header)
        print("-" * len(header))
        
        # Sort modules and functions for consistent output
        for module in sorted(cls._function_stats.keys()):
            for func_name in sorted(cls._function_stats[module].keys()):
                stats = cls._function_stats[module][func_name]
                print(f"{module:<{module_width}} | {func_name:<{func_width}} | {stats['calls']:>8} | "
                      f"{stats['total_time']:>15.6f} | {stats['avg_time']:>15.6f}")
        
        print("==================================\n")

def timer(func: F) -> F:
    """
    Decorator that measures and records the execution time of a function.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The wrapped function with timing functionality
    """
    module_name = func.__module__.split('.')[-1]
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            FunctionTimerRegistry.register_call(module_name, func.__name__, execution_time)
    
    return cast(F, wrapper) 