import yaml

class ConfigLoader:
    def __init__(self, filepath):
        self.filepath = filepath

    def load(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
