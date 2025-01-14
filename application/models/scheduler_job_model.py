from pydantic import BaseModel

class SchedulerJob(BaseModel):
    job_id: str
    trigger_type: str
    expression: dict
    queue: str
    message: str