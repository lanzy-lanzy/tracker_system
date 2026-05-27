#!/bin/bash
set -e

python -m pip install --break-system-packages -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
