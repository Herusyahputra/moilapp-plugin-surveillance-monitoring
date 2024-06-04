MAX_MONITOR_INDEX = 8
EMPTY_SLOTS = 8

class ModelAppsManager:
    def __init__(self):
        self.model_apps = [None] * 8

    def get_index_of_model_apps(self, element) -> int:
        try:
            index: int = self.model_apps.index(element)
            return index
        except ValueError:
            return -1

    def get_model_apps_by_index(self, index: int):
        return self.model_apps[index] if (0 <= index <= len(self.model_apps)) else None

    def get_empty_model_apps(self) -> list:
        return [i for i, slot in enumerate(self.model_apps) if slot is None]

    def get_in_use_model_apps(self) -> list:
        return [i for i, slot in enumerate(self.model_apps) if slot is not None]

    def set_model_apps(self, index: int, element):
        self.model_apps[index] = element if (0 <= index <= len(self.model_apps)) else None

    def clear_model_apps(self, index: int):
        self.model_apps[index] = None if (0 <= index <= len(self.model_apps)) else self.model_apps[index]