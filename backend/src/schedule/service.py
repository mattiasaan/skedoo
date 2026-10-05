import json
from typing import Dict
from pathlib import Path
from core.config import BASE_DIR
from .models import ClassSchedule


DATA_FOLDER = BASE_DIR / "data"
CLASSI_FOLDER = DATA_FOLDER / "classi"


class ScheduleService:
  def __init__(self):
    self._classes = self._load_classes()

  def _load_classes(self) -> Dict[str, ClassSchedule]:
    classes = {}

    #carica file tutte_le_classi.json se exists
    tutte_file = DATA_FOLDER / "tutte_le_classi.json"
    if tutte_file.exists():
      with open(tutte_file, "r", encoding="utf-8") as f:
        data = json.load(f)

        if isinstance(data, dict):
          for _, value in data.items():
            if "orario" not in value:
              continue
            schedule = ClassSchedule(**value)
            classes[schedule.id] = schedule

    #carica file dentro /classi
    if CLASSI_FOLDER.exists():
      for file in CLASSI_FOLDER.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
          data = json.load(f)

          if "orario" not in data:
            continue

          schedule = ClassSchedule(**data)
          classes[schedule.id] = schedule
    return classes

  def get_all(self):
    return self._classes

  def get_by_class(self, class_id: str):
    return self._classes.get(class_id)

  def get_by_class_and_day(self, class_id: str, day: str):
    schedule = self.get_by_class(class_id)
    if not schedule:
      return None

    return schedule.orario.get(day.lower())


schedule_service = ScheduleService()
