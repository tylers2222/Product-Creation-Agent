import structlog
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from product_agent.api.schemas.request import Job
from product_agent.infrastructure.llm.prompts import format_product_input

logger = structlog.get_logger(__name__)

async def consume_task(agent, redis, queue):
    """Function that points to the queue of tasks"""
    logger.info("Starting Task Consumer..")
    while True:
        task = await queue.get()
        # set up a binding logger to bind the request id
        logger.info("Starting task from the queue", task_id=task.request_id)

        try:
            query = format_product_input(task.body)

            # workflow returns a DraftResponse model we created
            resp = await agent.service_workflow(query, task.request_id)
            database_insert = redis.hset_data(database_name="agent:jobs", key=str(task.request_id), data=Job(completed=True, time_completed=resp.time_of_comepletion, url_of_job=resp.url).model_dump())
            logger.info(f"Successfully completed job from task queue", task_id=task.request_id, database_response=database_insert)
        except Exception as e:
            logger.error(f"Job from task queue failed", request_id=task.request_id, error=e, exc_info=True)
            insert = redis.hset_data(database_name="agent:jobs", key=str(task.request_id), data=Job(completed=False, error=str(e)).model_dump())
            logger.debug("Inserted redis data after failure", request_id=task.request_id)

        finally:
            logger.info(f"Marking task as done", request_id=task.request_id)
            queue.task_done()
