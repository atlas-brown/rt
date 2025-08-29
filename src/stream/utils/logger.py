import json
import os
import datetime
import traceback
from typing import Dict, List, Any, Optional
from stream.utils.function_timer import timer

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
        self._regex_logs: List[str] = []
        self._command_logs: Dict[str, int] = {}
        self._detailed_command_invocations: List[Dict[str, Any]] = []
        self._pattern_analysis_logs: List[Dict[str, Any]] = []
        self._command_pattern_logs: Dict[str, Dict[str, int]] = {}  # Track patterns by command and flag combination
        self._sed_pattern_logs: Dict[str, Dict[str, int]] = {}  # Track detailed sed patterns by flag combination
    
    def add_regex_log(self, regex: str) -> None:
        """
        Add a regex pattern to the regex logs.
        
        Args:
            regex: The regex pattern to add
        """
        self._regex_logs.append(regex)
    
    def add_command_log(self, command: str, count: int = 1) -> None:
        """
        Add or update a command in the command logs.
        
        Args:
            command: The command to log
            count: The count to set or add (defaults to 1)
        """
        if command in self._command_logs:
            self._command_logs[command] += count
        else:
            self._command_logs[command] = count
    
    def add_detailed_command_invocation(self, command_name: str, invocation: str, flags: List[str] = None, operands: List[str] = None) -> None:
        """
        Add a detailed command invocation to the log.
        
        Args:
            command_name: The name of the command (e.g., 'grep', 'cut', etc.)
            invocation: The full command invocation string
            flags: List of flags used in the command
            operands: List of operands used in the command
        """
        invocation_record = {
            "command_name": command_name,
            "invocation": invocation,
            "flags": flags or [],
            "operands": operands or [],
            "supported": None  # Will be set later during classification
        }
        self._detailed_command_invocations.append(invocation_record)
    
    def classify_last_invocation_as_supported(self) -> None:
        """
        Classify the last detailed command invocation as supported.
        """
        if self._detailed_command_invocations:
            self._detailed_command_invocations[-1]["supported"] = True
    
    def classify_last_invocation_as_unsupported(self) -> None:
        """
        Classify the last detailed command invocation as unsupported.
        """
        if self._detailed_command_invocations:
            self._detailed_command_invocations[-1]["supported"] = False
    
    def add_pattern_analysis(self, command_name: str, invocation: str, pattern: str, ast_repr: str, is_pure_string: bool, has_references: bool = False) -> None:
        """
        Add a pattern analysis record for grep or sed commands.
        
        Args:
            command_name: The command name ('grep' or 'sed')
            invocation: The full command invocation
            pattern: The regex pattern string
            ast_repr: String representation of the AST
            is_pure_string: Result of is_pure_string_for_ast check
            has_references: For sed, whether the replacement part has \ or & references
        """
        analysis_record = {
            "command_name": command_name,
            "invocation": invocation,
            "pattern": pattern,
            "ast_repr": ast_repr,
            "is_pure_string": is_pure_string,
            "has_references": has_references  # Only relevant for sed
        }
        self._pattern_analysis_logs.append(analysis_record)
    
    def update_last_pattern_analysis(self, pattern: str, ast_repr: str, is_pure_string: bool, has_references: bool = False) -> None:
        """
        Update the last pattern analysis record with pattern details.
        
        Args:
            pattern: The regex pattern string
            ast_repr: String representation of the AST
            is_pure_string: Result of is_pure_string_for_ast check
            has_references: For sed, whether the replacement part has \ or & references
        """
        if self._pattern_analysis_logs:
            last_record = self._pattern_analysis_logs[-1]
            last_record["pattern"] = pattern
            last_record["ast_repr"] = ast_repr
            last_record["is_pure_string"] = is_pure_string
            last_record["has_references"] = has_references
    
    def remove_last_pattern_analysis(self) -> None:
        """
        Remove the last pattern analysis record.
        """
        if self._pattern_analysis_logs:
            self._pattern_analysis_logs.pop()
    
    def add_command_pattern_log(self, command_name: str, flag_pattern: str) -> None:
        """
        Add or increment a command pattern based on command name and flag combination.
        
        Args:
            command_name: The command name (e.g., 'grep', 'cut', 'awk', 'sed', 'tr', 'paste', 'fmt')
            flag_pattern: The pattern of flags (e.g., '-w', '-wo', '-E', '-i', etc.)
        """
        try:
            if command_name not in self._command_pattern_logs:
                self._command_pattern_logs[command_name] = {}
            
            if flag_pattern not in self._command_pattern_logs[command_name]:
                self._command_pattern_logs[command_name][flag_pattern] = 0
            
            self._command_pattern_logs[command_name][flag_pattern] += 1
        except Exception as e:
            traceback.print_exc()
            exit(1)
    
    def get_flag_pattern_from_invocation(self, parsed_command_invocation) -> str:
        """
        Extract flag pattern from a command invocation.
        
        Args:
            parsed_command_invocation: The parsed command invocation
            
        Returns:
            str: The flag pattern (sorted flags concatenated)
        """
        try:
            flags = []
            for flag in parsed_command_invocation.flag_option_list:
                flags.append(flag.get_name())
            
            # Sort flags to ensure consistent pattern naming
            flags = list(set(flags))
            flags.sort()
            return "".join(flags) if flags else "(no_flags)"
        except Exception as e:
            traceback.print_exc()
            exit(1)
    
    def write_regex_logs_to_file(self, filepath: Optional[str] = None) -> str:
        """
        Write regex logs to a text file.
        
        Args:
            filepath: Path to the file where logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regex_logs_{timestamp}.txt"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for regex in self._regex_logs:
                f.write(f"{regex}\n")
        
        return filepath
    
    def write_command_logs_to_file(self, filepath: Optional[str] = None) -> str:
        """
        Write command logs to a file.
        
        Args:
            filepath: Path to the file where logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"command_logs_{timestamp}.json"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            sorted_logs = dict(sorted(self._command_logs.items(), key=lambda x: x[1], reverse=True))
            json.dump(sorted_logs, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def write_assertion_failure_stats_to_file(self, filepath: Optional[str] = None) -> str:
        """
        Calculate and write statistics about assertion failures among RT errors to a file.
        
        Args:
            filepath: Path to the file where statistics will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"assertion_stats_{timestamp}.json"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Calculate statistics
        total_rt_errors = 0
        assertion_failures = 0
        error_types = {}
        
        for record in self._logs:
            if record.get("RT_warning", False):
                total_rt_errors += 1
                error_type = record.get("error_type", "unknown")
                error_type = error_type.replace("tool error", "syntax error")
                
                if error_type in error_types:
                    error_types[error_type] += 1
                else:
                    error_types[error_type] = 1
                
                if error_type == "assertion failed":
                    assertion_failures += 1
        
        percentage = 0
        if total_rt_errors > 0:
            percentage = (assertion_failures / total_rt_errors) * 100
            
        stats = {
            "total_rt_errors": total_rt_errors,
            "assertion_failures": assertion_failures,
            "percentage": percentage,
            "error_types": error_types
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return filepath
    
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
    
    @timer
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
    
    def write_to_text(self, filepath: Optional[str] = None) -> str:
        """
        Write all logs to a text file in a readable format without JSON quotes and escaping.
        
        Args:
            filepath: Path to the text file where logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written text file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"log_{timestamp}.txt"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        def format_value(value, indent_level=0):
            indent = "  " * indent_level
            
            if isinstance(value, list):
                if not value:
                    return f"{indent}(empty list)"
                
                result = []
                for item in value:
                    if isinstance(item, (dict, list)):
                        # For nested dicts/lists, format with proper indentation
                        item_lines = format_value(item, indent_level + 1).split('\n')
                        result.append(f"{indent}- {item_lines[0]}")
                        result.extend([f"{indent}  {line}" for line in item_lines[1:]])
                    else:
                        result.append(f"{indent}- {item}")
                return '\n'.join(result)
            
            elif isinstance(value, dict):
                if not value:
                    return f"{indent}(empty dict)"
                
                result = []
                for k, v in value.items():
                    if isinstance(v, (dict, list)):
                        result.append(f"{indent}{k}:")
                        result.append(format_value(v, indent_level + 1))
                    else:
                        result.append(f"{indent}{k}: {v}")
                return '\n'.join(result)
            
            else:
                return f"{indent}{value}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write each log record as a readable text block
            for i, record in enumerate(self._logs):
                f.write(f"Record {i+1}:\n")
                for key, value in record.items():
                    if isinstance(value, (dict, list)):
                        f.write(f"{key}:\n")
                        f.write(format_value(value, 1) + '\n')
                    else:
                        f.write(f"{key}: {value}\n")
                f.write("\n")  # Add a blank line between records
        
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
    
    def write_detailed_command_invocations_to_file(self, filepath: Optional[str] = None, deduplicate: bool = False) -> str:
        """
        Write detailed command invocations to a text file with classification.
        Supported commands first, then unsupported, then unclassified, grouped by command name.
        
        Args:
            filepath: Path to the file where invocations will be written.
                     If None, a default path will be generated.
            deduplicate: If True, remove duplicate invocations (keep first occurrence)
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_command_invocations_{timestamp}.txt"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Get invocations (with optional deduplication)
        invocations = self._detailed_command_invocations
        if deduplicate:
            seen = set()
            deduplicated = []
            for inv in invocations:
                key = (inv["command_name"], inv["invocation"], inv["supported"])
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(inv)
            invocations = deduplicated
        
        # Separate supported, unsupported, and unclassified invocations
        supported_invocations = [inv for inv in invocations if inv["supported"] is True]
        unsupported_invocations = [inv for inv in invocations if inv["supported"] is False]
        unclassified_invocations = [inv for inv in invocations if inv["supported"] is None]
        
        # Group by command name
        def group_by_command(invocations):
            grouped = {}
            for inv in invocations:
                cmd_name = inv["command_name"]
                if cmd_name not in grouped:
                    grouped[cmd_name] = []
                grouped[cmd_name].append(inv)
            return grouped
        
        supported_grouped = group_by_command(supported_invocations)
        unsupported_grouped = group_by_command(unsupported_invocations)
        unclassified_grouped = group_by_command(unclassified_invocations)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("DETAILED COMMAND INVOCATIONS LOG\n")
            f.write("=" * 50 + "\n\n")
            
            # Write supported commands first
            f.write("SUPPORTED COMMANDS\n")
            f.write("-" * 30 + "\n\n")
            
            if supported_grouped:
                for cmd_name in sorted(supported_grouped.keys()):
                    f.write(f"Command: {cmd_name}\n")
                    f.write("~" * (len(cmd_name) + 9) + "\n")
                    for inv in supported_grouped[cmd_name]:
                        f.write(f"  Invocation: {inv['invocation']}\n")
                        f.write("\n")
                    f.write("\n")
            else:
                f.write("  No supported commands recorded.\n\n")
            
            # Write unsupported commands
            f.write("UNSUPPORTED COMMANDS\n")
            f.write("-" * 32 + "\n\n")
            
            if unsupported_grouped:
                for cmd_name in sorted(unsupported_grouped.keys()):
                    f.write(f"Command: {cmd_name}\n")
                    f.write("~" * (len(cmd_name) + 9) + "\n")
                    for inv in unsupported_grouped[cmd_name]:
                        f.write(f"  Invocation: {inv['invocation']}\n")
                        f.write("\n")
                    f.write("\n")
            else:
                f.write("  No unsupported commands recorded.\n\n")
            
            # Write unclassified commands
            f.write("UNCLASSIFIED COMMANDS\n")
            f.write("-" * 35 + "\n\n")
            
            if unclassified_grouped:
                for cmd_name in sorted(unclassified_grouped.keys()):
                    f.write(f"Command: {cmd_name}\n")
                    f.write("~" * (len(cmd_name) + 9) + "\n")
                    for inv in unclassified_grouped[cmd_name]:
                        f.write(f"  Invocation: {inv['invocation']}\n")
                        f.write("\n")
                    f.write("\n")
            else:
                f.write("  No unclassified commands recorded.\n\n")
            
            # Write summary statistics
            f.write("SUMMARY\n")
            f.write("-" * 15 + "\n")
            f.write(f"Total invocations: {len(invocations)}\n")
            f.write(f"Supported: {len(supported_invocations)}\n")
            f.write(f"Unsupported: {len(unsupported_invocations)}\n")
            f.write(f"Unclassified: {len(unclassified_invocations)}\n")
            if deduplicate:
                f.write(f"Original total (before deduplication): {len(self._detailed_command_invocations)}\n")
        
        return filepath
    
    def write_detailed_command_invocations_to_csv(self, filepath: Optional[str] = None, deduplicate: bool = False) -> str:
        """
        Write detailed command invocations to a CSV file, sorted by command name.
        
        Args:
            filepath: Path to the CSV file where invocations will be written.
                     If None, a default path will be generated.
            deduplicate: If True, remove duplicate invocations (keep first occurrence)
            
        Returns:
            str: Path to the written CSV file
        """
        import csv
        
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_command_invocations_{timestamp}.csv"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Get invocations (with optional deduplication)
        invocations = self._detailed_command_invocations
        if deduplicate:
            seen = set()
            deduplicated = []
            for inv in invocations:
                key = (inv["command_name"], inv["invocation"], inv["supported"])
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(inv)
            invocations = deduplicated
        
        # Sort by command name
        invocations_sorted = sorted(invocations, key=lambda x: x["command_name"])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['command_name', 'invocation', 'classification']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for inv in invocations_sorted:
                classification = 'supported' if inv['supported'] is True else ('unsupported' if inv['supported'] is False else 'unclassified')
                writer.writerow({
                    'command_name': inv['command_name'],
                    'invocation': inv['invocation'],
                    'classification': classification
                })
        
        return filepath
    
    def write_pattern_analysis_to_file(self, filepath: Optional[str] = None) -> str:
        """
        Write pattern analysis logs to a text file, grouped and sorted by command.
        For sed: commands with references first, then by pure string status
        For grep: non-pure strings first, then pure strings
        
        Args:
            filepath: Path to the file where analysis will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pattern_analysis_{timestamp}.txt"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Group by command name
        grouped = {}
        for record in self._pattern_analysis_logs:
            cmd_name = record["command_name"]
            if cmd_name not in grouped:
                grouped[cmd_name] = []
            grouped[cmd_name].append(record)
        
        # Sort each group according to the rules
        for cmd_name, records in grouped.items():
            if cmd_name == "sed":
                # For sed: references first, then by pure string status (non-pure first)
                records.sort(key=lambda x: (not x["has_references"], x["is_pure_string"]))
            else:  # grep and others
                # For grep: non-pure strings first
                records.sort(key=lambda x: x["is_pure_string"])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("PATTERN ANALYSIS LOG\n")
            f.write("=" * 40 + "\n\n")
            
            for cmd_name in sorted(grouped.keys()):
                records = grouped[cmd_name]
                f.write(f"Command: {cmd_name.upper()}\n")
                f.write("-" * (len(cmd_name) + 9) + "\n\n")
                
                for i, record in enumerate(records, 1):
                    f.write(f"  {i}. Invocation: {record['invocation']}\n")
                    f.write(f"     Pattern: {record['pattern']}\n")
                    f.write(f"     AST: {record['ast_repr']}\n")
                    f.write(f"     Is Pure String: {record['is_pure_string']}\n")
                    if record['command_name'] == 'sed':
                        f.write(f"     Has References (\\, &): {record['has_references']}\n")
                    f.write("\n")
                
                f.write("\n")
            
            # Write summary statistics
            f.write("SUMMARY\n")
            f.write("-" * 15 + "\n")
            f.write(f"Total patterns analyzed: {len(self._pattern_analysis_logs)}\n")
            for cmd_name in sorted(grouped.keys()):
                records = grouped[cmd_name]
                pure_count = sum(1 for r in records if r["is_pure_string"])
                f.write(f"{cmd_name}: {len(records)} total, {pure_count} pure strings, {len(records) - pure_count} non-pure\n")
                if cmd_name == "sed":
                    ref_count = sum(1 for r in records if r["has_references"])
                    f.write(f"         {ref_count} with references, {len(records) - ref_count} without references\n")
        
        return filepath
    
    def write_pattern_analysis_to_csv(self, filepath: Optional[str] = None) -> str:
        """
        Write pattern analysis logs to a CSV file, grouped by command with sorting within each group.
        
        Args:
            filepath: Path to the CSV file where analysis will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written CSV file
        """
        import csv
        
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pattern_analysis_{timestamp}.csv"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Group by command name
        grouped = {}
        for record in self._pattern_analysis_logs:
            cmd_name = record["command_name"]
            if cmd_name not in grouped:
                grouped[cmd_name] = []
            grouped[cmd_name].append(record)
        
        # Sort each group according to the rules
        for cmd_name, records in grouped.items():
            if cmd_name == "sed":
                # For sed: references first, then by pure string status (non-pure first)
                records.sort(key=lambda x: (not x["has_references"], x["is_pure_string"]))
            else:  # grep and others
                # For grep: non-pure strings first
                records.sort(key=lambda x: x["is_pure_string"])
        
        # Prepare sorted records by group
        sorted_records = []
        for cmd_name in sorted(grouped.keys()):
            sorted_records.extend(grouped[cmd_name])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['command_name', 'invocation', 'pattern', 'ast_repr', 'is_pure_string', 'has_references']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in sorted_records:
                writer.writerow(record)
        
        return filepath
    
    def write_command_pattern_logs_to_file(self, filepath: Optional[str] = None) -> str:
        """
        Write command pattern logs to a text file.
        
        Args:
            filepath: Path to the file where pattern logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written file
        """
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"command_pattern_logs_{timestamp}.txt"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("COMMAND PATTERN LOGS\n")
            f.write("=" * 40 + "\n\n")
            
            for command_name in sorted(self._command_pattern_logs.keys()):
                patterns = self._command_pattern_logs[command_name]
                f.write(f"Command: {command_name.upper()}\n")
                f.write("-" * (len(command_name) + 9) + "\n\n")
                
                # Sort patterns by count (descending) then by pattern name
                sorted_patterns = sorted(patterns.items(), key=lambda x: (-x[1], x[0]))
                
                for pattern, count in sorted_patterns:
                    f.write(f"  Pattern: {pattern}\n")
                    f.write(f"  Count: {count}\n\n")
                
                f.write("\n")
            
            # Write summary statistics
            f.write("SUMMARY\n")
            f.write("-" * 15 + "\n")
            total_patterns = sum(len(patterns) for patterns in self._command_pattern_logs.values())
            total_invocations = sum(sum(patterns.values()) for patterns in self._command_pattern_logs.values())
            f.write(f"Total unique patterns: {total_patterns}\n")
            f.write(f"Total invocations: {total_invocations}\n")
            for command_name in sorted(self._command_pattern_logs.keys()):
                patterns = self._command_pattern_logs[command_name]
                cmd_patterns = len(patterns)
                cmd_invocations = sum(patterns.values())
                f.write(f"{command_name}: {cmd_patterns} patterns, {cmd_invocations} invocations\n")
        
        return filepath
    
    def write_command_pattern_logs_to_csv(self, filepath: Optional[str] = None) -> str:
        """
        Write command pattern logs to a CSV file.
        
        Args:
            filepath: Path to the CSV file where pattern logs will be written.
                     If None, a default path will be generated.
            
        Returns:
            str: Path to the written CSV file
        """
        import csv
        
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"command_pattern_logs_{timestamp}.csv"
            logs_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, filename)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['command_name', 'flag_pattern', 'count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for command_name in sorted(self._command_pattern_logs.keys()):
                patterns = self._command_pattern_logs[command_name]
                # Sort patterns by count (descending) then by pattern name
                sorted_patterns = sorted(patterns.items(), key=lambda x: (-x[1], x[0]))
                
                for pattern, count in sorted_patterns:
                    writer.writerow({
                        'command_name': command_name,
                        'flag_pattern': pattern,
                        'count': count
                    })
        
        return filepath
    
    def add_sed_command_pattern_log(self, parsed_command_invocation) -> None:
        """
        Add sed command pattern log by analyzing both flags and operands directly in logger.
        
        Args:
            parsed_command_invocation: The parsed command invocation for sed
        """
        try:
            # Get flag pattern
            flag_pattern = self.get_flag_pattern_from_invocation(parsed_command_invocation)
            
            # Get operands directly
            operands = []
            for operand in parsed_command_invocation.operand_list:
                operands.append(operand.name)
            
            # Analyze operand pattern for sed and count each pattern separately
            if operands:
                # Handle multiple patterns separated by semicolons
                if operands[0].startswith('s;'):
                    pattern_type = "unknown_pattern"
                    combined_key = f"{flag_pattern}:{pattern_type}"
                    self.add_command_pattern_log("sed", combined_key)
                    return
                patterns = operands[0].split(";")
                pattern_counts = {}
                
                for pattern in patterns:
                    pattern = pattern.strip()
                    if not pattern:
                        continue
                        
                    pattern_type = self._classify_single_sed_pattern(pattern)
                    
                    # Create combined key with flag pattern
                    combined_key = f"{flag_pattern}:{pattern_type}"
                    
                    # Count this pattern
                    if combined_key not in pattern_counts:
                        pattern_counts[combined_key] = 0
                    pattern_counts[combined_key] += 1
                
                # Add each pattern count to the log
                for combined_key, count in pattern_counts.items():
                    for _ in range(count):
                        self.add_command_pattern_log("sed", combined_key)
            else:
                self.add_command_pattern_log("sed", flag_pattern)
                
        except Exception as e:
            traceback.print_exc()
            exit(1)
    
    def _classify_single_sed_pattern(self, pattern: str) -> str:
        """
        Classify a single sed pattern.
        
        Args:
            pattern: A single sed pattern
            
        Returns:
            str: The pattern classification
        """
        try:
            import re
            
            # Pattern for substitution s<delimiter>pattern<delimiter>replacement<delimiter>[flags]
            # Adaptive delimiter: any non-alphanumeric character after 's'
            if len(pattern) >= 2 and pattern[0] == 's':
                delimiter = pattern[1]
                template = fr"^s{delimiter}.*{delimiter}.*{delimiter}(g|p|q)*$"
                if re.match(template, pattern):
                    return "s/.*/.*/g?p?q?"
                else:
                    return "unknown_pattern"
            
            if re.match(r'^/[^/]*/((!d)|d|p|q)+$', pattern):
                return "/.*/((!d)|d|p|q)+"
            
            # Range deletion like 1,5d or 1,$d  
            if re.match(r'^([0-9]+(,[0-9$]+)?)?((!d)|d|p|q)+$', pattern):
                return "([0-9]+(,[0-9$]+)?)?((!d)|d|p|q)+"
            
            
            # Any other patterns - return the original pattern for analysis
            return "unknown_pattern"
            
        except Exception as e:
            traceback.print_exc()
            return pattern


# Global function to get the singleton instance
@timer
def get_logger() -> LogManager:
    """
    Get the singleton LogManager instance.
    
    Returns:
        LogManager: The singleton LogManager instance
    """
    return LogManager() 