import os
import sys

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import structlog
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from agents.agent.agent import create_agent, AgentProtocol
from agents.agent.prompts import format_product_input

from api.models.request_schema import Job
from api.shared import queue
from api.routers.product_generate import router
from api.internal.consume_task import consume_task

from db.client import RedisDatabase, KV_DB

logger = structlog.get_logger(__name__)

def create_app(agent: AgentProtocol | None = None, job_database: KV_DB | None = None, agent_job_queue: asyncio.Queue | None = None, start_consumer = True) -> FastAPI:
    logger.info("Started Creating App")

    def init_lifespan(agent, job_database):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            app.state.agent_service = create_agent() if agent is None else agent
            app.state.job_db = RedisDatabase(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT"))) if job_database is None else job_database
            app.state.queue = queue if agent_job_queue is None else agent_job_queue

            try:
                app.state.job_db.ping()
            except Exception as e:
                print("="*60)
                print("🚨"*60)
                print()
                print("REDIS CONNECNTION FAILED")
                print()
                print("🚨"*60)
                print("="*60)

            if start_consumer:
                message = asyncio.create_task(consume_task(app.state.agent_service, app.state.job_db, app.state.queue))
            yield

            if start_consumer:
                message.cancel()
                try:
                    await message
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    pass

        return lifespan

    app = FastAPI(lifespan=init_lifespan(agent=agent, job_database=job_database))
    app.include_router(router=router)

    logger.info("Created App")
    return app

