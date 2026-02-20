"""Product routes — thin HTTP layer.

Each route does one thing: parse request, call handler, return response.
Dependencies injected via FastAPI's built-in Depends().
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.commands.product_commands import (
    CreateProductCommand,
    DeleteProductCommand,
    GenerateDescriptionCommand,
    UpdateProductCommand,
)
from ...application.handlers.command_handlers import (
    CreateProductCommandHandler,
    DeleteProductCommandHandler,
    GenerateDescriptionCommandHandler,
    UpdateProductCommandHandler,
)
from ...application.handlers.query_handlers import (
    GetGenerationHistoryQueryHandler,
    GetProductQueryHandler,
    ListProductsQueryHandler,
)
from ...application.queries.product_queries import (
    GetGenerationHistoryQuery,
    GetProductQuery,
    ListProductsQuery,
)
from ...dependencies import get_cache, get_event_publisher, get_history_repo, get_llm_service, get_uow
from ...domain.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from ..schemas.request import AIDescriptionRequest, ProductCreateRequest, ProductUpdateRequest
from ..schemas.response import GenerationHistoryResponse, ProductListResponse, ProductResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    uow=Depends(get_uow),
    cache=Depends(get_cache),
    events=Depends(get_event_publisher),
    llm=Depends(get_llm_service),
    history=Depends(get_history_repo),
):
    handler = CreateProductCommandHandler(uow, events, cache, llm, history)
    try:
        product = await handler.handle(CreateProductCommand(**request.model_dump()))
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProductResponse.model_validate(product)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = 0, limit: int = 100, category: str | None = None,
    uow=Depends(get_uow),
):
    handler = ListProductsQueryHandler(uow)
    products, total = await handler.handle(ListProductsQuery(skip=skip, limit=limit, category=category))
    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, uow=Depends(get_uow), cache=Depends(get_cache)):
    handler = GetProductQueryHandler(uow, cache)
    try:
        product = await handler.handle(GetProductQuery(product_id=product_id))
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, request: ProductUpdateRequest,
    uow=Depends(get_uow), cache=Depends(get_cache), events=Depends(get_event_publisher),
):
    handler = UpdateProductCommandHandler(uow, events, cache)
    try:
        product = await handler.handle(UpdateProductCommand(product_id=product_id, **request.model_dump()))
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    uow=Depends(get_uow), cache=Depends(get_cache), events=Depends(get_event_publisher),
):
    handler = DeleteProductCommandHandler(uow, events, cache)
    try:
        await handler.handle(DeleteProductCommand(product_id=product_id))
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.post("/generate-description")
async def generate_description(
    request: AIDescriptionRequest,
    llm=Depends(get_llm_service), history=Depends(get_history_repo),
):
    handler = GenerateDescriptionCommandHandler(llm, history)
    description = await handler.handle(GenerateDescriptionCommand(**request.model_dump()))
    if not description:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM service unavailable")
    return {"description": description}


@router.get("/{product_id}/generation-history", response_model=list[GenerationHistoryResponse])
async def get_generation_history(product_id: int, history=Depends(get_history_repo)):
    handler = GetGenerationHistoryQueryHandler(history)
    records = await handler.handle(GetGenerationHistoryQuery(product_id=product_id))
    return [GenerationHistoryResponse.model_validate(r) for r in records]
