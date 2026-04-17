from typing import Dict, List, Any, Optional
import os
import yaml
from pathlib import Path


class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"
        self.EVALUATION_DIR = self.PROJECT_ROOT / "evaluation_results"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        os.makedirs(self.EVALUATION_DIR, exist_ok=True)
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        
        # Define default output paths
        default_with_annotation_dir = self.EVALUATION_DIR / "with_annotations"
        default_raw_dir = self.EVALUATION_DIR / "raw"
        
        self._default_config = {
            "enable_timeout": False,
            "timeout_seconds": 10,
            "enable_user_annotation": True,
            "annotation_disabled_dirs": [],
            "num_workers": 1,
            
            "enable_rule_no_empty_output": True,
            "enable_rule_no_ignored_input": True,
            "enable_rule_no_meaningless_command": True,
            "enable_rule_no_sort_non_numeric_with_numeric_input": True,
            
            "evaluation_notes_path": str(self.PROJECT_ROOT / "evaluation_notes.json"),
            "parsing_error_log_path": str(self.LOGS_DIR / "parsing_errors.log"),
            "shellcheck_command": "shellcheck",
            "ltsh_command": "ltsh",
            "ltsh_typedb_path": "ltsh_config/typedb",
            
            # Output paths with annotations
            "output_results_path_with_annotation": str(default_with_annotation_dir / "evaluation_results.json"),
            "output_summary_path_with_annotation": str(default_with_annotation_dir / "summary.csv"),
            
            # Output paths without annotations
            "output_results_path_raw": str(default_raw_dir / "evaluation_results.json"),
            "output_summary_path_raw": str(default_raw_dir / "summary.csv"),
            
            # Legacy paths (for backward compatibility)
            "output_results_path": str(default_with_annotation_dir / "evaluation_results.json"),
            "output_summary_path": str(default_with_annotation_dir / "summary.csv"),
            
            "valid_dirs": [
                "./evaluation_pipelines/valid",
                "./full_benchmark/intercode/pipelines",
                "./full_benchmark/pash_benchmark/benchmarks/unix50/scripts"
            ],
            "invalid_dirs": [
                "./evaluation_pipelines/invalid",
                "./full_benchmark/curated_mutants",
                "./full_benchmark/llm_injection/pipelines"
            ],
            "not_check_all_dirs": [],
            
            "log_level": "INFO",

            "enable_FST": True
        }
        
        self._config = self._load_config(os.path.join(self.CONFIG_DIR, "config.yaml"))
        
        # Create output directories
        os.makedirs(os.path.dirname(self._config["output_results_path_with_annotation"]), exist_ok=True)
        os.makedirs(os.path.dirname(self._config["output_summary_path_with_annotation"]), exist_ok=True)
        os.makedirs(os.path.dirname(self._config["output_results_path_raw"]), exist_ok=True)
        os.makedirs(os.path.dirname(self._config["output_summary_path_raw"]), exist_ok=True)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        config = self._default_config.copy()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = yaml.safe_load(f)
                config.update(user_config)
            except Exception as e:
                print(f"Error loading configuration from {config_path}: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self._config[key] = value
    
    def reload(self) -> None:
        self._config = self._load_config(os.path.join(self.CONFIG_DIR, "config.yaml"))


CONFIG = Config() 
