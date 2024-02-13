#!/bin/bash
export PYTHONPATH=/task_manager:$PYTHONPATH

#alembic revision --autogenerate -m 'create tables'
alembic upgrade head

python commands/fill_database.py
python commands/createsuperuser.py --username=admin --password=admin --email=admin@ya.ru

uvicorn main:app --host 0.0.0.0 --port 8000

