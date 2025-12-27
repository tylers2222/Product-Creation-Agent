import logging
import sys
import json
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Response, Depends
from ..models.request_schema import RequestSchema, Job
from ..models.product_generation import PromptVariant
from ..dependencies.product_generation_dependencies import get_job_database, get_queue

router = APIRouter()

logging.basicConfig(level=logging.INFO)

@router.get("/")
async def read_root():
    return {"Hello": "World"}

@router.get("/internal/product_generation/{job_id}")
async def get_job_status(job_id: str, redis = Depends(get_job_database)):
    """Used prediminently by GUI to poll for their job requests"""
    logging.info(f"Started get_job_status with job_id -> {job_id}")
    try:
        data = redis.hget_data(database_name="agent:jobs", key=job_id)
        if data is None:
            # need some systematic alert to say why is this happening, major error to have a GUI asking for a job id and it not existing
            # could potentially poll forever if no timeout is added on the GUI polling for results
            return

        content = json.dumps({"data": data.decode("utf-8"), "message": "Successfully delivered data"})
        return Response(content=content, status_code=200)
    except Exception as e:
        # if redis goes down, not being able to search from redis should potentially panic the whole program
        # originally did raise HTTPException(status_code=400, detail={"message": "Contact admin for support quoting your product and job id"})
        sys.exit(f"Failed to search redis {e} -> job_id = {job_id}")

@router.post("/internal/product_generation")
async def process_internal_query(query: PromptVariant, redis = Depends(get_job_database), queue = Depends(get_queue)):
    """Route to process agent assistance"""
    try:
        request_id = uuid.uuid4()
        time_request = datetime.datetime.now()
        logging.info(f"Recieved request for agent workflow at {time_request} -> request_id: {request_id}")

        request_schema = RequestSchema(
            request_id=str(request_id),
            created_at=time_request,
            body=query
        )
        await queue.put(request_schema)
        
        job = Job(completed=False)
        redis.hset_data(database_name="agent:jobs", key=str(request_id), data=job.model_dump())

        content = json.dumps({"request_id": str(request_id)})
        return Response(content=content, status_code=200)

    except Exception as e:
        logging.error(f"Job {request_id} failed -> {e}", exc_info=True)
        raise HTTPException(status_code=400, detail={"message": "Failed to queue your task, contact admin with your wanted request and job id", "job_id": request_id})
