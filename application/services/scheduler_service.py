import pika
import os
from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging
import pytz

load_dotenv()

engine = create_engine(os.getenv('DB_SERVER_URL'))

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScheduleService")

class ScheduleService:
    def __init__(self):
        # Configuración de los JobStores
        self.jobstores = {
            "default": SQLAlchemyJobStore(engine=engine)
        }

        # Configuración de los ejecutores
        self.executors = {
            "default": ThreadPoolExecutor(20)
        }

        # Configuración por defecto para los jobs
        self.job_defaults = {
            "coalesce": True,       # Combina ejecuciones perdidas en una sola
            "max_instances": 1,     # Solo una instancia del job puede ejecutarse a la vez
            "misfire_grace_time": 60  # Tiempo de gracia de 60 segundos para ejecuciones perdidas
        }

        # Configuración del scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=self.jobstores,
            executors=self.executors,
            job_defaults=self.job_defaults,
            timezone=pytz.timezone("Etc/GMT-3")
        )

        # Iniciar el scheduler
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        logger.info("Scheduler iniciado correctamente.")

    def job_listener(self, event):
        """
        Listener para eventos de ejecución de trabajos.
        """
        if event.exception:
            logger.error(f"Error en el trabajo: {event.job_id}")
        else:
            logger.info(f"Trabajo ejecutado con éxito: {event.job_id}")

    def add(self, config):
        """
        Añade un nuevo trabajo al scheduler.
        """
        try:
            logger.info(f"Identificando trigger: {config.trigger_type}")
            trigger = self.get_trigger(config)
            logger.info(f"Añadiendo trabajo: {config.job_id}")
            job = self.scheduler.add_job(
                func=execute_job,
                trigger=trigger,
                id=config.job_id,
                args=[config.__dict__],
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=60
            )
            logger.info(f"Trabajo {config.job_id} añadido: {job}")
            return {"message": "Job added", "job_id": config.job_id}
        except Exception as e:
            logger.error(f"Error al añadir el trabajo: {e}")
            return {"message": "Error adding job", "error": str(e)}

    def delete_job(self, job_id):
        """
        Elimina un trabajo del scheduler.
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Trabajo {job_id} eliminado.")
            return {"message": "Job deleted", "job_id": job_id}
        except Exception as e:
            logger.error(f"Error al eliminar el trabajo {job_id}: {e}")
            return {"message": "Error deleting job", "error": str(e)}

    def get(self, job_id):
        """
        Obtiene los detalles de un trabajo programado.
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    "job_id": job.id,
                    "next_run_time": str(job.next_run_time),
                    "trigger": str(job.trigger)
                }
            return {"message": "Job not found", "job_id": job_id}
        except Exception as e:
            logger.error(f"Error al obtener el trabajo {job_id}: {e}")
            return {"message": "Error getting job", "error": str(e)}

    def get_scheduled_jobs(self):
        """
        Obtiene todos los trabajos programados.
        """
        try:
            jobs = self.scheduler.get_jobs()
            job_list = [
                {
                    "job_id": job.id,
                    "next_run_time": str(job.next_run_time),
                    "trigger": str(job.trigger)
                }
                for job in jobs
            ]
            return {"jobs": job_list}
        except Exception as e:
            logger.error(f"Error al obtener trabajos programados: {e}")
            return {"message": "Error getting scheduled jobs", "error": str(e)}


    def get_trigger(self, config):
        """
        Devuelve el tipo de trigger según la configuración.
        """
        if config.trigger_type == "interval":
            return IntervalTrigger(**config.expression)
        elif config.trigger_type == "cron":
            return CronTrigger(**config.expression)
        elif config.trigger_type == "date":
            return DateTrigger(run_date=config.expression["run_date"])
        else:
            raise ValueError("Trigger type no válido")

    def pickle_schedule(self):
        """
        Guarda el estado del scheduler.
        """
        try:
            self.scheduler.shutdown(wait=False)  # Detenemos el scheduler de forma segura
            logger.info("Scheduler guardado correctamente.")
        except Exception as e:
            logger.error(f"Error al guardar el estado del scheduler: {e}")
    
def execute_job(config):
    """
    Función que se ejecuta como parte de los trabajos: Envía un mensaje a RabbitMQ.
    """
    try:
        logger.info(f"Ejecutando el trabajo: {config['job_id']}")

        # Configuración de conexión a RabbitMQ
        connection_params = pika.URLParameters(os.getenv('RABBIT_SERVER_URL'))
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Publicación del mensaje en la cola
        channel.queue_declare(queue=config["queue"], durable=True)  # Asegurar que la cola existe
        channel.basic_publish(
            exchange='',
            routing_key=config["queue"],
            body=config["message"],
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer el mensaje persistente
            )
        )
        logger.info(f"Mensaje enviado a la cola {config['queue']}: {config['message']}")

        # Cerrar conexión
        connection.close()
    except Exception as e:
        logger.error(f"Error al ejecutar el trabajo {config['job_id']}: {e}")
