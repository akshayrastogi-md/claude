"""
Sales API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models import SalesRecord, Product
from app.schemas.sales import SalesRecordCreate, SalesRecordResponse

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SalesRecordResponse, status_code=status.HTTP_201_CREATED)
def create_sales_record(record: SalesRecordCreate, db: Session = Depends(get_db)):
    """Create a new sales record"""

    # Verify product exists
    product = db.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {record.product_id} not found"
        )

    db_record = SalesRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record


@router.post("/bulk", response_model=List[SalesRecordResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_sales(records: List[SalesRecordCreate], db: Session = Depends(get_db)):
    """Create multiple sales records at once"""

    db_records = []
    for record in records:
        # Verify product exists
        product = db.query(Product).filter(Product.id == record.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {record.product_id} not found"
            )

        db_record = SalesRecord(**record.model_dump())
        db.add(db_record)
        db_records.append(db_record)

    db.commit()
    for record in db_records:
        db.refresh(record)

    return db_records


@router.get("/", response_model=List[SalesRecordResponse])
def list_sales(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    sales_channel: str = None,
    db: Session = Depends(get_db)
):
    """List sales records with optional filters"""

    from sqlalchemy import and_

    query = db.query(SalesRecord)

    filters = []
    if product_id:
        filters.append(SalesRecord.product_id == product_id)

    if start_date:
        filters.append(SalesRecord.sale_date >= start_date)

    if end_date:
        filters.append(SalesRecord.sale_date <= end_date)

    if sales_channel:
        filters.append(SalesRecord.sales_channel == sales_channel)

    if filters:
        query = query.filter(and_(*filters))

    records = query.order_by(SalesRecord.sale_date.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/product/{product_id}", response_model=List[SalesRecordResponse])
def get_product_sales(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get sales history for a specific product"""

    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    records = db.query(SalesRecord).filter(
        SalesRecord.product_id == product_id
    ).order_by(SalesRecord.sale_date.desc()).offset(skip).limit(limit).all()

    return records
