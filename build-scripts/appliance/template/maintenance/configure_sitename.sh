#!/usr/bin/env bash
echo ""
echo "================================================================"
echo " Final configuration for SITENAME "
echo "================================================================"
echo ""
echo "- Create 'admin' superuser for Django admin"
echo ""
cd SOURCE_DIR
../virtualenv/bin/python3 manage.py createsuperuser --username admin
echo ""
echo "--- Finished configuration"
echo ""
