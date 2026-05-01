import time
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Any

class Timing:
    # Class-level data storage grouped by label
    _timing_data: Dict[str, List[Dict]] = defaultdict(list)
    _output_files: Dict[str, str] = {}
    _statistics: Dict[str, Dict] = defaultdict(lambda: {
        'count': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0
    })
    
    def __init__(self, label: str, output_file: str, skip_on_error: bool = False):
        """Initialize Timing object with label and output file
        
        Args:
            label: Label for grouping timing data
            output_file: File to write timing data  
            skip_on_error: If True, don't record timing when exceptions occur
        """
        self.label = label
        self.output_file = output_file
        self.skip_on_error = skip_on_error
        self.start = None
        self.message = None
        self.extra_data = {}
        
        # Map label to output file
        Timing._output_files[label] = output_file
    
    def __call__(self, message: Optional[str] = None, **kwargs):
        """Set message and extra data when used as context manager"""
        self.message = message
        self.extra_data = kwargs
        return self
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, exn_type, exn_value, exn_tb):
        elapsed_secs = time.time() - self.start
        
        # Skip recording if error occurred and skip_on_error is True
        if self.skip_on_error and exn_type is not None:
            return False
        
        # Record timing data
        timing_record = {
            'elapsed_time': elapsed_secs,
            'timestamp': time.time()
        }
        
        # Add message only if it's not None
        if self.message is not None:
            timing_record['message'] = self.message
        
        # Add any extra key-value pairs
        timing_record.update(self.extra_data)
        
        # Add error information if exception occurred
        if exn_type is not None:
            timing_record['error'] = True
            timing_record['error_type'] = exn_type.__name__
        
        # Store record and update statistics
        Timing._timing_data[self.label].append(timing_record)
        self._update_statistics(elapsed_secs)
        
        return False
    
    def _update_statistics(self, elapsed_time: float):
        """Incrementally update statistics"""
        stats = Timing._statistics[self.label]
        stats['count'] += 1
        stats['total_time'] += elapsed_time
        stats['min_time'] = min(stats['min_time'], elapsed_time)
        stats['max_time'] = max(stats['max_time'], elapsed_time)
    
    def finish(self):
        """Write all data to file - call this at the end"""
        self._write_to_file()
    
    def _write_to_file(self):
        """Write timing data to output file"""
        if self.label in Timing._output_files:
            output_file = Timing._output_files[self.label]
            
            # Ensure directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Write all data and statistics for this label
            data = {
                'label': self.label,
                'records': Timing._timing_data[self.label],
                'statistics': self._get_statistics()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_statistics(self) -> Dict:
        """Get precomputed statistics for current label"""
        stats = Timing._statistics[self.label]
        if stats['count'] == 0:
            return {}
        
        return {
            'count': stats['count'],
            'total_time': stats['total_time'],
            'average_time': stats['total_time'] / stats['count'],
            'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0.0,
            'max_time': stats['max_time']
        }
    
    @classmethod
    def get_statistics(cls, label: str) -> Dict:
        """Get statistics for specified label"""
        if label not in cls._statistics or cls._statistics[label]['count'] == 0:
            return {}
        
        stats = cls._statistics[label]
        return {
            'label': label,
            'count': stats['count'],
            'total_time': stats['total_time'],
            'average_time': stats['total_time'] / stats['count'],
            'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0.0,
            'max_time': stats['max_time'],
            'records': cls._timing_data[label]
        }
    
    @classmethod
    def clear_data(cls, label: Optional[str] = None):
        """Clear data for specified label or all data if None"""
        if label:
            if label in cls._timing_data:
                del cls._timing_data[label]
            if label in cls._output_files:
                del cls._output_files[label]
            if label in cls._statistics:
                del cls._statistics[label]
        else:
            cls._timing_data.clear()
            cls._output_files.clear()
            cls._statistics.clear()
    
    @classmethod
    def get_all_labels(cls) -> List[str]:
        """Get all registered labels"""
        return list(cls._timing_data.keys())
    
    @classmethod
    def finish_all(cls):
        """Write all timing data to their respective files"""
        for label in cls._timing_data.keys():
            if label in cls._output_files:
                # Create a temporary timer instance for writing
                temp_timer = cls.__new__(cls)
                temp_timer.label = label
                temp_timer._write_to_file()
