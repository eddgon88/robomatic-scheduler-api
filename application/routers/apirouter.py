from fastapi import APIRouter
from application.models.scheduler_job_model import SchedulerJob
from application.services.scheduler_service import ScheduleService

router = APIRouter(prefix="/scheduler/v1")

# Instancia única del scheduler - se inicializa de forma diferida
schedule: ScheduleService = None


@router.on_event("startup")
async def load_schedule_or_create_blank():
    """
    Inicializa el Schedule Object como parámetro global.
    Se usa inicialización diferida para evitar múltiples instancias.
    """
    global schedule

    try:
        if schedule is None:
            print("Creating Schedule Object")
            schedule = ScheduleService()
            print("Schedule Object created successfully")
    except Exception as e:
        print(f"Unable to Create Schedule Object: {e}")


@router.on_event("shutdown")
async def pickle_schedule():
    if schedule:
        schedule.pickle_schedule()


@router.post("/schedule", status_code=200)
async def add_job(config: SchedulerJob):
    return schedule.add(config)


@router.delete("/schedule/{job_id}", status_code=200)
async def delete_job(job_id):
    """
    Remove a Job from a Schedule
    """
    return schedule.delete_job(job_id)


@router.get("/schedule/{job_id}", status_code=200)
async def get_job(job_id):
    """
    Get a Job from a Schedule with job_id
    """
    return schedule.get(job_id)


@router.get("/schedules/get-jobs/", status_code=200)
async def get_scheduled_jobs():
    """
    Will provide a list of currently Scheduled Tasks
    """
    return schedule.get_scheduled_jobs()
