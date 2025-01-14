from fastapi import APIRouter
from application.models.scheduler_job_model import SchedulerJob
from application.services.scheduler_service import ScheduleService

router = APIRouter(prefix="/scheduler/v1")
schedule = ScheduleService()

#@router.on_event("startup")
#async def load_schedule_or_create_blank():
#    """
#    Instatialise the Schedule Object as a Global Param and also load existing Schedules from SQLite
#    This allows for persistent schedules across server restarts. 
#    """
#    global Schedule
#
#    try:
#        jobstores = {
#            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
#        }
#        Schedule = BackgroundScheduler(jobstores=jobstores)
#        Schedule.start()
#        #logger.info("Created Schedule Object")   
#    except:    
#        #logger.error("Unable to Create Schedule Object")   
#        print("Unable to Create Schedule Object")

@router.on_event("shutdown")
async def pickle_schedule():
    schedule.pickle_schedule


@router.post("/schedule", status_code=200)
async def add_job(config: SchedulerJob):
    #print("Consuming: " + config.engine)
    #scheduled_job = Schedule.add_job(executeJob, config.trigger_type, minute=config.expression,id=config.job_id,args=[config.queue, config.message], replace_existing=True)
    return schedule.add(config)

@router.delete("/schedule/{job_id}", status_code=200)
async def delete_job(job_id):
    """
    Remove a Job from a Schedule
    """
    #Schedule.remove_job(job_id)
    #return {"scheduled":False,"job_id":job_id}
    return schedule.delete_job(job_id)

@router.get("/schedule/{job_id}", status_code=200)
async def get_job(job_id):
    """
    get a Job from a Schedule with job_id
    """
    #job = Schedule.get_job(job_id)
    #job_dict = {"job_id": str(job.id), "run_frequency": str(job.trigger), "next_run": str(job.next_run_time)}
    #return job_dict
    return schedule.get(job_id)

@router.get("/schedules/get-jobs/", status_code=200)
async def get_scheduled_jobs():
    """
    Will provide a list of currently Scheduled Tasks
    """
    #schedules = []
    #for job in Schedule.get_jobs():
    #    schedules.append({"job_id": str(job.id), "run_frequency": str(job.trigger), "next_run": str(job.next_run_time)})
    #return {"jobs":schedules}
    return schedule.get_scheduled_jobs()