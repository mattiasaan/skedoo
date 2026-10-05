from fastapi import APIRouter, HTTPException
from typing import Dict
from .schemas import ScheduleResponse, DayScheduleResponse
from .service import schedule_service
from .models import ClassSchedule

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/", response_model=Dict[str, ScheduleResponse])
def get_all_schedules():
  return schedule_service.get_all()


@router.get("/{class_id}", response_model=ScheduleResponse)
def get_class_schedule(class_id: str):
  schedule = schedule_service.get_by_class(class_id)

  if not schedule:
    raise HTTPException(status_code=404, detail="Classe non trovata")

  return schedule


@router.get("/{class_id}/{day}", response_model=DayScheduleResponse)
def get_schedule_by_day(class_id: str, day: str):
  day_schedule = schedule_service.get_by_class_and_day(class_id, day)

  if not day_schedule:
    raise HTTPException(status_code=404, detail="Classe o giorno nn trovato")

  return {

    "classe": class_id,
    "giorno": day.lower(),
    "orario": day_schedule
  }