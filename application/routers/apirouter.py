from fastapi import APIRouter
from pydantic import BaseModel
import pika
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
import os

load_dotenv()


class SchedulerJob(BaseModel):
    job_id: str
    trigger_type: str
    expression: str
    queue: str
    message: str

router = APIRouter(prefix="/scheduler/v1")


@router.on_event("startup")
async def load_schedule_or_create_blank():
    """
    Instatialise the Schedule Object as a Global Param and also load existing Schedules from SQLite
    This allows for persistent schedules across server restarts. 
    """
    global Schedule

    try:
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        Schedule = BackgroundScheduler(jobstores=jobstores)
        Schedule.start()
        #logger.info("Created Schedule Object")   
    except:    
        #logger.error("Unable to Create Schedule Object")   
        print("Unable to Create Schedule Object")

@router.on_event("shutdown")
async def pickle_schedule():
    """
    An Attempt at Shutting down the schedule to avoid orphan jobs
    """
    global Schedule
    Schedule.shutdown()
    print("Disabled Schedule")


@router.post("/schedule", status_code=200)
async def add_job(config: SchedulerJob):
    #print("Consuming: " + config.engine)
    scheduled_job = Schedule.add_job(executeJob, config.trigger_type, minute=config.expression,id=config.job_id,args=[config.queue, config.message], replace_existing=True)
    return {"scheduled":True,"job_id":scheduled_job.id}

@router.delete("/schedule/{job_id}", status_code=200)
async def delete_job(job_id):
    """
    Remove a Job from a Schedule
    """
    Schedule.remove_job(job_id)
    return {"scheduled":False,"job_id":job_id}

@router.get("/schedule/{job_id}", status_code=200)
async def get_job(job_id):
    """
    get a Job from a Schedule with job_id
    """
    job = Schedule.get_job(job_id)
    job_dict = {"job_id": str(job.id), "run_frequency": str(job.trigger), "next_run": str(job.next_run_time)}
    return job_dict

@router.get("/schedules/get-jobs/", status_code=200)
async def get_scheduled_jobs():
    """
    Will provide a list of currently Scheduled Tasks
    """
    schedules = []
    for job in Schedule.get_jobs():
        schedules.append({"job_id": str(job.id), "run_frequency": str(job.trigger), "next_run": str(job.next_run_time)})
    return {"jobs":schedules}

def executeJob(queue, message):
    params = pika.URLParameters(os.getenv('RABBIT_SERVER_URL'))
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)  # Connect to CloudAMQP
    channel = connection.channel()  # start a channel
    channel.queue_declare(queue=queue)
    # send a message

    channel.basic_publish(
        exchange='', routing_key=queue, body=str(message))
    print("[x] Message sent to consumer")
    connection.close()