import uuid, os
from celery import Celery
from celery import states
from celery.signals import (
    task_sent,
    task_success,
    task_failure,
    task_prerun,
    task_postrun,
)
from app.models.models import MLModel, ModelRegistryModel, UserModel, JobsModel
from app.constants import InstanceType as instance_type
from app.constants import SageMakerConstants as sm_constants
from app.core.SagemakerManager import SagemakerManager
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure Celery to use the Redis broker
broker_url = os.getenv("RABBITMQ_URI")

worker = Celery("model_registry_worker", broker=broker_url)


@worker.task(bind=True)
def register_model_worker(self, user_uuid: str, model_uuid: str) -> tuple:
    self.request.kwargs = {"user_uuid": user_uuid}

    sm = SagemakerManager(bucket_name=sm_constants.BUCKET_NAME, role=sm_constants.ROLE)

    record = MLModel.get_record_by_uuid(model_uuid)
    if not record:
        raise Exception(f"Model with UUID {model_uuid} not found")
    
    model = sm.create_model(model_path=record.s3_url, model_type=record.model_type)

    dummy_uuid_generator = str(uuid.uuid4())

    endpoint_name = sm.deploy_model(
        model=model,
        instance_type=instance_type.CPU,
        endpoint_name=f"dummy-endpoint-{dummy_uuid_generator}",
    ).endpoint_name

    return model_uuid, endpoint_name


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    user_uuid = kwargs["args"][0]
    if user_uuid:
        JobsModel.save_job_to_db(
            job_uuid=task_id,
            user_uuid=user_uuid,
            job_type="model_registry",
            job_status=states.STARTED,
            reference_uuid=None,
        )
    else:
        logging.error("User UUID is missing")


@task_success.connect
def task_success_handler(sender=None, result=None, *args, **kwargs):
    model_uuid, model_endpoint = result
    task_id = sender.request.id

    model_registry_uuid = ModelRegistryModel.register_model(
        model_uuid=model_uuid,
        model_version="1.0",
        model_status=states.SUCCESS,
        model_endpoint=model_endpoint,
    )

    JobsModel.update_task_status(task_id, states.SUCCESS)
    JobsModel.update_task_reference(task_id, model_registry_uuid)


@task_failure.connect
def task_failure_handler(task_id, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.FAILURE)
