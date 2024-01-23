from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.api.db import TaskStatus


def filter_like(field, value):
    return [field.ilike(f"%{value}%")]


def filter_status(field, value):
    if value.upper() in TaskStatus.__members__:
        return [field == value.upper()]
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid status value"
        )


def filter_date(field, value):
    try:
        date_start = datetime.strptime(value, "%Y-%m-%d")
        date_end = date_start + timedelta(days=1)
        return [field >= date_start, field < date_end]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format"
        )


def filter_exact(field, value):
    return [field == value]
