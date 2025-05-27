import os
from fastapi import APIRouter, HTTPException, Depends, Response
from sqlmodel import select
from typing import List
from connection import get_session
from util.auth import authenticate_user
from models.task_model import Task, TaskCreate, TaskWithFullDetails, TaskParse
from models.user_model import User
import httpx

router = APIRouter(prefix="/tasks", tags=["tasks"])
PARSER_URL = os.environ.get('PARSER_URL', "http://localhost:1800")

@router.post("/", response_model=Task)
def create_task(task: TaskCreate, current_user: User = Depends(authenticate_user), session=Depends(get_session)):
    if not current_user.is_organizer:
        raise HTTPException(status_code=403, detail="Only organizers can create tasks")
    new_task = Task(**task.dict(), user_id=current_user.id)
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskWithFullDetails])
def list_tasks(session=Depends(get_session)):
    return session.exec(select(Task)).all()


@router.get("/{task_id}", response_model=TaskWithFullDetails)
def get_task(task_id: int, session=Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/parse")
async def proxy_parse(req: TaskParse) -> Response:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f'{PARSER_URL}/parse', json=req.model_dump())
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502,
                                detail=f"Parser service error: {exc}")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
        headers={k: v for k, v in resp.headers.items()
                 if k.lower().startswith("content-")},
    )


@router.post("/parse_async")
async def proxy_parse(req: TaskParse) -> Response:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f'{PARSER_URL}/parse_async', json=req.model_dump())
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502,
                                detail=f"Parser service error: {exc}")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
        headers={k: v for k, v in resp.headers.items()
                 if k.lower().startswith("content-")},
    )


@router.get("/parse_tasks/{task_id}")
async def proxy_parse(task_id: str) -> Response:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f'{PARSER_URL}/tasks/{task_id}')
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502,
                                detail=f"Parser service error: {exc}")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
        headers={k: v for k, v in resp.headers.items()
                 if k.lower().startswith("content-")},
    )
