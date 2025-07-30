import os
import yaml

class GetConfigs:
    def get_configs(self):
        # Get the absolute path to the config.yaml file
        # Assuming the config.yaml is located in the src/core directory
        config_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'config.yaml')
        # Ensure the path is absolute
        config_path = os.path.abspath(config_path)
        # Load and return the configurations from the YAML file
        with open(config_path) as f:
            return yaml.safe_load(f)
