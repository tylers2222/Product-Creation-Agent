import structlog
import sys
import json
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Response, Depends
from ..models.request_schema import RequestSchema, Job
from ..models.product_generation import PromptVariant
from ..dependencies.product_generation_dependencies import get_job_database, get_queue

router = APIRouter()

logger = structlog.get_logger(__name__)

@router.get("/")
async def read_root():
    return {"Hello": "World"}

@router.get("/internal/product_generation/{job_id}")
async def get_job_status(job_id: str, redis = Depends(get_job_database)):
    """Used prediminently by GUI to poll for their job requests"""
    logger.debug("Started get_job_status", job_id=job_id)
    try:
        redis_return_data = redis.hget_data(database_name="agent:jobs", key=job_id)
        if redis_return_data is None:
            # need some systematic alert to say why is this happening, major error to have a GUI asking for a job id and it not existing
            # could potentially poll forever if no timeout is added on the GUI polling for results
            return

        logger.debug("Redis return data type", type=type(redis_return_data))
        logger.debug("Redis return data", data=redis_return_data)
        logger.info("Success retrieved redis data", job_id=job_id)
        content = json.dumps({"data": redis_return_data.decode("utf-8"), "message": "Successfully delivered data"})
        return Response(content=content, status_code=200)
    except Exception as e:
        # if redis goes down, not being able to search from redis should potentially panic the whole program
        raise HTTPException(status_code=400, detail={"message": "Contact admin for support quoting your product and job id"})

@router.post("/internal/product_generation")
async def process_internal_query(query: PromptVariant, redis = Depends(get_job_database), queue = Depends(get_queue)):
    """Route to process agent assistance"""
    logger.debug("Started on the route process_internal_query", query=query.model_dump_json())
    try:
        request_id = uuid.uuid4()
        request_id = str(request_id)
        logger.info(f"Recieved request for agent workflow", job_id=str(request_id))

        request_schema = RequestSchema(
            request_id=str(request_id),
            created_at=datetime.datetime.now(),
            body=query
        )

        logger.debug("Request Schema to send to queue", request_schema=request_schema, job_id=str(request_id))
        await queue.put(request_schema)
        logger.debug("Request Schema sent to queue")
        
        job = Job(completed=False)
        redis.hset_data(database_name="agent:jobs", key=str(request_id), data=job.model_dump())

        logger.info("Successfully sent task to queue", job_id=str(request_id))
        content = json.dumps({"request_id": str(request_id)})
        return Response(content=content, status_code=200)

    except Exception as e:
        logger.error("Task Failed To Queue", job_id=str(request_id), exc_info=True)
        raise HTTPException(status_code=400, detail={"message": "Failed to queue your task, contact admin with your wanted request and job id", "job_id": request_id})
