import json

_config = None
_config_path = 'src/stream/evaluation_config.json'
def get_config():
    global _config
    if _config:
        return _config
    with open(_config_path, 'r') as f:
        _config = json.load(f)
        return _config
