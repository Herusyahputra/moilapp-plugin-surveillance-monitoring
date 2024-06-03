MAX_MONITOR_INDEX: int = 8
EMPTY_SLOTS: int = 8

class ModelAppsManager:
    def __init__(self):
        self.slots = [None] * 8

    def get_index_of_slot(self, element) -> int:
        try:
            index: int = self.slots.index(element)
            return index
        except ValueError:
            return -1

    def get_slot_by_index(self, index: int):
        return self.slots[index] if (0 <= index <= len(self.slots)) else None

    def get_empty_slots(self) -> list:
        return [i for i, slot in enumerate(self.slots) if slot is None]

    def get_used_slots(self) -> list:
        return [i for i, slot in enumerate(self.slots) if slot is not None]

    def set_slot(self, index: int, element):
        self.slots[index] = element if (0 <= index <= len(self.slots)) else None

    def clear_slot(self, index: int):
        self.slots[index] = None if (0 <= index <= len(self.slots)) else self.slots[index]