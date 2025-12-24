import logging
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api.models.request_schema import Job
from agents.agent.prompts import format_product_input

async def consume_task(agent, redis, queue):
    """Function that points to the queue of tasks"""
    while True:
        task = await queue.get()
        # set up a binding logger to bind the request id
        logging.info(f"Starting task from the queue -> task_id: {task.request_id}")

        try:
            query = format_product_input(task.body)

            # workflow returns a DraftResponse model we created
            resp = await agent.service_workflow(query)
            database_insert = redis.hset_data(database_name="agent:jobs", key=str(task.request_id), data=Job(completed=True, time_completed=resp.time_of_comepletion, url_of_job=resp.url).model_dump())
            logging.info(f"Successfully completed job {task.request_id} -> Database Response: {database_insert}")
        except Exception as e:
            logging.error(f"Job {task.request_id} failed, {e}", exc_info=True)
            insert = redis.hset_data(database_name="agent:jobs", key=str(task.request_id), data=Job(completed=False, error=str(e)).model_dump())

        finally:
            logging.info(f"Marking task {task.request_id} as done")
            queue.task_done()
