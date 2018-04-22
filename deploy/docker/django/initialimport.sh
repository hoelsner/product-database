#!/usr/bin/env bash

cd /var/www/productdb/source
python3 manage.py initialimport $@