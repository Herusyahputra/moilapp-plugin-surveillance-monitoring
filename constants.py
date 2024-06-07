from typing import *

MAX_MONITOR_INDEX: int  = 8
EMPTY_SLOTS: int        = 8
RECORDING_FPS: float    = 30.00

# Constant label image WIDTH and HEIGHT
# NOTE: Works for only 1920x1080 display devices
LABEL_IMAGE_WIDTH: int  = 340
LABEL_IMAGE_HEIGHT: int = 260

LATEST_MOVED_WIDGET: list[dict[str, int, None]] = [None] * MAX_MONITOR_INDEX
AVAILABLE_MONITORS: list[Optional[int]]         = [0] * MAX_MONITOR_INDEX

class ModelAppsManager:
    def __init__(self):
        self.model_apps = [None] * 8

    def get_index_of_model_apps(self, element) -> int:
        try:
            index: int = self.model_apps.index(element)
            return index
        except ValueError: return -1

    def get_model_apps_by_index(self, index: int) -> Optional[int]:
        return self.model_apps[index] if (0 <= index <= len(self.model_apps)) else None

    def get_empty_model_apps(self) -> list[Optional[int]]:
        return [i for i, slot in enumerate(self.model_apps) if slot is None]

    def get_in_use_model_apps(self) -> list[Optional[int]]:
        return [i for i, slot in enumerate(self.model_apps) if slot is not None]

    def set_model_apps(self, index: int, element) -> None:
        self.model_apps[index] = element if (0 <= index <= len(self.model_apps)) else None

    def clear_model_apps(self, index: int) -> None:
        self.model_apps[index] = None if (0 <= index <= len(self.model_apps)) else self.model_apps[index]
