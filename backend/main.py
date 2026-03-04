from fastapi import FastAPI
from schedule.routes import router as schedules_router

app = FastAPI()

app.include_router(schedules_router)