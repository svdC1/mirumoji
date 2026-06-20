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
from ..models.requests import SubmitBatchRequest, SubmitJobRequest
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
        error_code=job.error_code,
        error_details=job.error_details,
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
    LOGGER.info(
        f"Job '{job.id}' ('{job.type}') Submitted For Profile '{profile_id}'"
    )
    return _to_response(job)


@jobs_router.post(
    "/batch",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
)
async def submit_batch(
    req: SubmitBatchRequest,
    profile_id: str = Depends(ensure_profile_exists),
    manager: JobQueueManager = Depends(get_job_manager),
) -> JobResponse:
    """
    Submits a batch job that runs one operation across several profile files

    info: How It Works
        - Creates a parent job + one `queued` child job per `file_id`

        - enqueues the parent, and returns it for the client to track

        - The worker runs the parent, which either runs the children in
          parallel or one at a time depending on the handler

        - Per-file status lives on the children, reachable via
          `GET /jobs/{id}/children`

    Args:
        req (SubmitBatchRequest): The batch submission
        profile_id (str): Validated profile id
        manager (JobQueueManager): The job worker

    Returns:
        The created parent job (`202 Accepted`)

    Raises:
        HTTPException: If a `file_id` is malformed or not owned by the profile
        DatabaseError: If persistence fails
    """
    file_uuids: list[uuid.UUID] = []
    for file_id in req.file_ids:
        try:
            file_uuids.append(uuid.UUID(file_id))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid File Id '{file_id}'",
            ) from e

    async with UnitOfWork() as uow:
        for file_uuid in file_uuids:
            file_rec = await uow.files.get(file_uuid)
            if file_rec.profile_id != profile_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File Not Found",
                )
        parent = await uow.jobs.add(
            profile_id=profile_id,
            type=req.type,
            params=req.to_params(),
            total=len(req.file_ids),
        )
        for file_id in req.file_ids:
            await uow.jobs.add(
                profile_id=profile_id,
                type=req.child_type(),
                params=req.child_params(file_id),
                parent_id=parent.id,
            )
        await uow.commit()

    await manager.submit_job(parent.id)
    LOGGER.info(
        f"Batch '{parent.id}' ('{parent.type}') Submitted For Profile "
        f"'{profile_id}' Over {len(req.file_ids)} File(s)"
    )
    return _to_response(parent)


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


@jobs_router.get("/{job_id}/children", response_model=list[JobResponse])
async def list_job_children(
    job_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> list[JobResponse]:
    """
    Lists the per-file child jobs of a batch parent owned by the profile

    Single-op jobs have no children and return an empty list

    Args:
        job_id (uuid.UUID): The parent job id
        profile_id (str): Validated profile id

    Returns:
        The child jobs, in submit order

    Raises:
        HTTPException: If the parent isn't owned by the profile
        RecordNotFoundError: If the parent does not exist
        DatabaseError: If the query fails
    """
    async with UnitOfWork() as uow:
        parent = await uow.jobs.get(job_id)
        if parent.profile_id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job Not Found",
            )
        children = await uow.jobs.list_children(job_id)
    return [_to_response(child) for child in children]


@jobs_router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
) -> JobResponse:
    """
    Cancels a queued or running job owned by the active profile

    info: How Cancellation Works
        - A queued job is skipped by the worker when it would otherwise run

        - A running job is marked cancelled on a best-effort basis (it may
          still finish)

        - Cancelling a batch parent cascades to its still-active children

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
            children = await uow.jobs.list_children(job_id)
            for child in children:
                if child.status in ("queued", "running"):
                    await uow.jobs.update(child.id, status="cancelled")
            LOGGER.info(f"Job '{job_id}' Cancel Requested")
        await uow.commit()
    return _to_response(job)


@jobs_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    profile_id: str = Depends(ensure_profile_exists),
    manager: JobQueueManager = Depends(get_job_manager),
) -> None:
    """
    Deletes a finished job owned by the active profile (its record, not its
    produced files)

    A batch parent's child jobs are removed with it. A job that is still active
    (`queued` / `running`) or still being finished by the worker (a `cancelled`
    job whose handler has not returned yet) is refused, so the worker is never
    left holding a deleted row

    Args:
        job_id (uuid.UUID): The job id
        profile_id (str): Validated profile id
        manager (JobQueueManager): The job worker

    Raises:
        HTTPException: If the job isn't owned by the profile, or is still
            active or in flight
        RecordNotFoundError: If the job does not exist
        DatabaseError: If the deletion fails
    """
    async with UnitOfWork() as uow:
        job = await uow.jobs.get(job_id)
        if job.profile_id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job Not Found",
            )
        if (
            job.status in ("queued", "running")
            or job_id == manager.running_job_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The Job Is Still Finishing, Try Again In A Moment",
            )
        await uow.jobs.delete(job_id)
        await uow.commit()
    LOGGER.info(f"Job '{job_id}' Deleted For Profile '{profile_id}'")
