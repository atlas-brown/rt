# Configuration System

This directory contains configuration files for the Stream project, providing a centralized way to manage settings across the application using a singleton pattern.

## Files

- `global_config.py`: Contains the singleton configuration class
- `config.json`: User-customizable configuration values

## Usage

The configuration is implemented as a singleton class that can be accessed from anywhere in the code:

```python
from src.stream.config import CONFIG

# Access configuration values
timeout_seconds = CONFIG.get("timeout_seconds", 10)  # Provides a default fallback
enable_user_annotation = CONFIG["enable_user_annotation"]  # Direct access

# Access project paths
project_root = CONFIG.PROJECT_ROOT
config_dir = CONFIG.CONFIG_DIR

# Get evaluation pipeline paths
valid_dirs = CONFIG["valid_dirs"]
invalid_dirs = CONFIG["invalid_dirs"]
not_check_all_dirs = CONFIG["not_check_all_dirs"]

# Set the output paths
CONFIG["output_results_path_with_annotation"] = "evaluation_results/with_annotations/evaluation_results.json"
CONFIG["output_summary_path_with_annotation"] = "evaluation_results/with_annotations/summary.csv"
CONFIG["output_results_path_raw"] = "evaluation_results/raw/evaluation_results.json"
CONFIG["output_summary_path_raw"] = "evaluation_results/raw/summary.csv"
```

## Customizing Configuration

You can customize the configuration by editing the `config.json` file. The configuration includes:

1. Evaluation settings (timeout, workers, etc.)
2. File paths (output files, notes)
3. Pipeline paths for evaluation
4. Logging settings

The singleton will automatically load this file and merge settings with the defaults.

## Reloading Configuration

If you need to reload the configuration at runtime:

```python
from src.stream.config import CONFIG

# After making changes to config.json
CONFIG.reload()
``` 