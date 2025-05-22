import json
import os
import datetime
from typing import Dict, List, Any, Optional


class LogManager:
    """
    A singleton log manager class that can create new records,
    get references to the latest records, and write logs to JSON files.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the log manager."""
        self._logs: List[Dict[str, Any]] = []
    
    def create_record(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new log record with timestamp and additional fields.
        
        Args:
            **kwargs: Key-value pairs to include in the log record
            
        Returns:
            Dict[str, Any]: Reference to the created log record
        """
        # timestamp = datetime.datetime.now().isoformat()
        record = {
            # "timestamp": timestamp,
            **kwargs
        }
        self._logs.append(record)
        return record
    
    def get_latest_record(self) -> Optional[Dict[str, Any]]:
        """
        Get a reference to the latest log record.
        
        Returns:
            Optional[Dict[str, Any]]: Reference to the latest log record or None if no records exist
        """
        if not self._logs:
            return None
        return self._logs[-1]
    
    def remove_latest_record(self) -> None:
        """
        Remove the latest log record.
        """
        if not self._logs:
            return
        self._logs.pop()
    
    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all log records.
        
        Returns:
            List[Dict[str, Any]]: List of all log records
        """
        return self._logs
    
    def clear_logs(self) -> None:
        """
        Clear all log records.
        """
        self._logs.clear()
    
    def generate_default_filepath(self) -> str:
        """
        Generate a default filepath for log files.
        
        Returns:
            str: A default filepath for log files
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"log_{timestamp}.json"
        
        # Create a logs directory in the current working directory
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        return os.path.join(logs_dir, filename)
    
    def write_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Write all logs to a JSON file.
        
        Args:
            filepath: Path to the JSON file where logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written JSON file
        """
        if filepath is None:
            filepath = self.generate_default_filepath()
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._logs, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_from_json(self, filepath: str, append: bool = False) -> List[Dict[str, Any]]:
        """
        Load logs from a JSON file.
        
        Args:
            filepath: Path to the JSON file to load logs from
            append: If True, append loaded logs to existing logs; if False, replace existing logs
            
        Returns:
            List[Dict[str, Any]]: The loaded log records
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_logs = json.load(f)
                
            if not isinstance(loaded_logs, list):
                raise ValueError("Loaded JSON is not a list of records")
                
            if append:
                self._logs.extend(loaded_logs)
            else:
                self._logs = loaded_logs
                
            return self._logs
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading logs from {filepath}: {e}")
            return []
    
    def update_record(self, record: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Update an existing log record with new values.
        
        Args:
            record: The record to update
            **kwargs: Key-value pairs to update in the record
            
        Returns:
            Dict[str, Any]: Reference to the updated record
        """
        if record in self._logs:
            record.update(kwargs)
        return record
    
    @staticmethod
    def write_object_to_json(obj: Any, filepath: str) -> str:
        """
        Write any object to a JSON file.
        
        Args:
            obj: Any object that can be serialized to JSON
            filepath: Path to the JSON file where the object will be written
            
        Returns:
            str: Path to the written JSON file
        """
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    @staticmethod
    def load_object_from_json(filepath: str) -> Any:
        """
        Load an object from a JSON file.
        
        Args:
            filepath: Path to the JSON file to load the object from
            
        Returns:
            Any: The loaded object
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading object from {filepath}: {e}")
            return None


# Global function to get the singleton instance
def get_logger() -> LogManager:
    """
    Get the singleton LogManager instance.
    
    Returns:
        LogManager: The singleton LogManager instance
    """
    return LogManager() 