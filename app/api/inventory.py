"""
Inventory API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models import InventoryRecord, Product
from app.schemas.inventory import InventoryRecordCreate, InventoryRecordResponse

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/", response_model=InventoryRecordResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_record(record: InventoryRecordCreate, db: Session = Depends(get_db)):
    """Create a new inventory record"""

    # Verify product exists
    product = db.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {record.product_id} not found"
        )

    db_record = InventoryRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record


@router.get("/", response_model=List[InventoryRecordResponse])
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    warehouse_id: str = None,
    db: Session = Depends(get_db)
):
    """List inventory records with optional filters"""

    query = db.query(InventoryRecord)

    if product_id:
        query = query.filter(InventoryRecord.product_id == product_id)

    if warehouse_id:
        query = query.filter(InventoryRecord.warehouse_id == warehouse_id)

    records = query.order_by(InventoryRecord.recorded_at.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/current", response_model=List[InventoryRecordResponse])
def get_current_inventory(db: Session = Depends(get_db)):
    """Get current inventory levels (latest record for each product)"""

    from sqlalchemy import func, and_

    # Get latest inventory record for each product
    subquery = db.query(
        InventoryRecord.product_id,
        func.max(InventoryRecord.recorded_at).label('max_date')
    ).group_by(InventoryRecord.product_id).subquery()

    current_inventory = db.query(InventoryRecord).join(
        subquery,
        and_(
            InventoryRecord.product_id == subquery.c.product_id,
            InventoryRecord.recorded_at == subquery.c.max_date
        )
    ).all()

    return current_inventory


@router.get("/product/{product_id}", response_model=List[InventoryRecordResponse])
def get_product_inventory_history(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get inventory history for a specific product"""

    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    records = db.query(InventoryRecord).filter(
        InventoryRecord.product_id == product_id
    ).order_by(InventoryRecord.recorded_at.desc()).offset(skip).limit(limit).all()

    return records
