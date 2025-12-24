from fastapi import Request

def get_agent(request: Request):
    return request.app.state.agent_service

def get_job_database(request: Request):
    return request.app.state.job_db

def get_queue(request: Request):
    return request.app.state.queue