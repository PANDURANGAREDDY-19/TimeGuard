#!/usr/bin/env bash
pip install -r requirements.txt
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH
python init_db.py