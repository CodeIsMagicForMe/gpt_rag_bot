"""Node management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit_event
from ..crud import create_node, delete_entity, get_entity, list_entities, update_node
from ..dependencies import get_current_active_user, get_db_session, get_request_ip
from ..models import Node, User
from ..schemas import NodeCreate, NodeRead, NodeUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("/", response_model=list[NodeRead])
async def list_nodes(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
    offset: int = 0,
    limit: int = 50,
) -> list[NodeRead]:
    nodes = await list_entities(session, Node, offset=offset, limit=limit)
    return [NodeRead.model_validate(node) for node in nodes]


@router.post("/", response_model=NodeRead, status_code=201)
async def create_node_endpoint(
    data: NodeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> NodeRead:
    node = await create_node(session, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="node_create",
        target_type="node",
        target_id=str(node.id),
        metadata=data.model_dump(),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(node)
    return NodeRead.model_validate(node)


@router.get("/{node_id}", response_model=NodeRead)
async def get_node_endpoint(
    node_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_active_user),
) -> NodeRead:
    node = await get_entity(session, Node, node_id)
    return NodeRead.model_validate(node)


@router.put("/{node_id}", response_model=NodeRead)
async def update_node_endpoint(
    node_id: int,
    data: NodeUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> NodeRead:
    node = await get_entity(session, Node, node_id)
    node = await update_node(session, node, data)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="node_update",
        target_type="node",
        target_id=str(node.id),
        metadata=data.model_dump(exclude_unset=True),
        ip_address=ip,
    )
    await session.commit()
    await session.refresh(node)
    return NodeRead.model_validate(node)


@router.delete("/{node_id}", status_code=204)
async def delete_node_endpoint(
    node_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    ip: str | None = Depends(get_request_ip),
) -> None:
    node = await get_entity(session, Node, node_id)
    await delete_entity(session, Node, node_id)
    await record_audit_event(
        session,
        actor_user_id=current_user.id,
        action="node_delete",
        target_type="node",
        target_id=str(node_id),
        metadata={"name": node.name},
        ip_address=ip,
    )
    await session.commit()
