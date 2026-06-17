"""
This module defines the `jobs_router` of the Mirumoji API

Exposes endpoints for submitting a long-running operation which uses an
existing profile file, and tracking its status by polling

Attributes:
    LOGGER (logging.Logger): Module's logging object
    jobs_router (APIRouter): The FastAPI router object
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from ..db import UnitOfWork
from ..db.models import JobDTO
from ..dependencies import ensure_profile_exists, get_job_manager
from ..jobs import JobQueueManager
from ..models.requests import SubmitJobRequest
from ..models.responses import JobResponse

LOGGER = logging.getLogger(__name__)
jobs_router = APIRouter(prefix="/jobs")


def _to_response(job: JobDTO) -> JobResponse:
    """
    Maps a `JobDTO` to its API response shape

    Args:
        job (JobDTO): The job DTO

    Returns:
        The `JobResponse`
    """
    return JobResponse(
        id=str(job.id),
        type=job.type,
        status=job.status,
        progress=job.progress,
        total=job.total,
        completed=job.completed,
        parent_id=str(job.parent_id) if job.parent_id else None,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@jobs_router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
)
async def submit_job(
    req: SubmitJobRequest,
    profile_id: str = Depends(ensure_profile_exists),
    manager: JobQueueManager = Depends(get_job_manager),
) -> JobResponse:
    """
    Submits a long-running job to perform an operation on an existing profile
    file

    Creates a `queued` job referencing `req.file_id`, enqueues it, and returns
    immediately with the job to track. The worker then runs the operation

    Args:
        req (SubmitJobRequest): The job submission
        profile_id (str): Validated profile id
        manager (JobQueueManager): The job worker

    Returns:
        The created job (`202 Accepted`)

    Raises:
        HTTPException: If `file_id` is malformed or not owned by the profile
        DatabaseError: If persistence fails
    """
    try:
        file_uuid = uuid.UUID(req.file_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid File Id '{req.file_id}'",
        ) from e

    async with UnitOfWork() as uow:
        file_rec = await uow.files.get(file_uuid)
        if file_rec.profile_id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File Not Found",
            )
        job = await uow.jobs.add(
            profile_id=profile_id,
            type=req.type,
            params=req.to_params(),
        )
        await uow.commit()

    await manager.submit_job(job.id)
    return _to_response(job)


@jobs_router.get("", response_model=list[JobResponse])
async def list_jobs(
    active: bool = False,
    profile_id: str = Depends(ensure_profile_exists),
) -> list[JobResponse]:
    """
    Lists the active profile's top-level jobs (batch children are excluded)

    Args:
        active (bool): Restrict to `queued` / `running` jobs
        profile_id (str): Validated profile id

    Returns:
        The profile's jobs, newest first

    Raises:
        DatabaseError: If the query fails
    """
    async with UnitOfWork() as uow:
        jobs = await uow.jobs.list_for_profile(profile_id, active_only=active)
    return [_to_response(j) for j in jobs]


@jobs_router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> JobResponse:
    """
    Fetches a single job owned by the active profile

    Args:
        job_id (uuid.UUID): The job id
        profile_id (str): Validated profile id

    Returns:
        The job

    Raises:
        HTTPException: If the job isn't owned by the profile
        RecordNotFoundError: If the job does not exist
        DatabaseError: If the lookup fails
    """
    async with UnitOfWork() as uow:
        job = await uow.jobs.get(job_id)
    if job.profile_id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job Not Found",
        )
    return _to_response(job)


@jobs_router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> JobResponse:
    """
    Cancels a queued or running job owned by the active profile

    A queued job is skipped by the worker when it would otherwise run. A
    running job is marked cancelled on a best-effort basis (it may still
    finish)

    Args:
        job_id (uuid.UUID): The job id
        profile_id (str): Validated profile id

    Returns:
        The (possibly updated) job

    Raises:
        HTTPException: If the job isn't owned by the profile
        RecordNotFoundError: If the job does not exist
        DatabaseError: If the update fails
    """
    async with UnitOfWork() as uow:
        job = await uow.jobs.get(job_id)
        if job.profile_id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job Not Found",
            )
        if job.status in ("queued", "running"):
            job = await uow.jobs.update(job_id, status="cancelled")
        await uow.commit()
    return _to_response(job)
