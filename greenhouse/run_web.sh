#!/bin/bash
export PYTHONPATH=/home/pi/sand:/greenhouse/pip:/home/pi/.local/lib/python3.9/site-packages
echo $PYTHONPATH

python3.9 -Bu -m app
# gunicorn /home/pi/sand/app:app --workers 2