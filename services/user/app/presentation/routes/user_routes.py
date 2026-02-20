"""User routes — thin HTTP layer.

Each route does one thing: parse request, call handler, return response.
Dependencies injected via FastAPI's built-in Depends().
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.commands.user_commands import CreateUserCommand, DeleteUserCommand, UpdateUserCommand
from ...application.handlers.command_handlers import (
    CreateUserCommandHandler,
    DeleteUserCommandHandler,
    UpdateUserCommandHandler,
)
from ...application.handlers.query_handlers import GetUserQueryHandler, ListUsersQueryHandler
from ...application.queries.user_queries import GetUserQuery, ListUsersQuery
from ...dependencies import get_cache, get_event_publisher, get_uow
from ...domain.exceptions import UserAlreadyExistsError, UserNotFoundError
from ..schemas.request import UserCreateRequest, UserUpdateRequest
from ..schemas.response import UserListResponse, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    uow=Depends(get_uow), cache=Depends(get_cache), events=Depends(get_event_publisher),
):
    handler = CreateUserCommandHandler(uow, events, cache)
    try:
        user = await handler.handle(CreateUserCommand(**request.model_dump()))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UserResponse.model_validate(user)


@router.get("/", response_model=UserListResponse)
async def list_users(skip: int = 0, limit: int = 100, uow=Depends(get_uow)):
    handler = ListUsersQueryHandler(uow)
    users, total = await handler.handle(ListUsersQuery(skip=skip, limit=limit))
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, uow=Depends(get_uow), cache=Depends(get_cache)):
    handler = GetUserQueryHandler(uow, cache)
    try:
        user = await handler.handle(GetUserQuery(user_id=user_id))
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, request: UserUpdateRequest,
    uow=Depends(get_uow), cache=Depends(get_cache), events=Depends(get_event_publisher),
):
    handler = UpdateUserCommandHandler(uow, events, cache)
    try:
        user = await handler.handle(UpdateUserCommand(user_id=user_id, **request.model_dump()))
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    uow=Depends(get_uow), cache=Depends(get_cache), events=Depends(get_event_publisher),
):
    handler = DeleteUserCommandHandler(uow, events, cache)
    try:
        await handler.handle(DeleteUserCommand(user_id=user_id))
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
