#!/usr/bin/env bash
echo ""
echo "Start staging the Product Database"
echo "=================================="
echo ""
echo "Please Note: The ansible playbook is only tested with Ubuntu 16.04 and uses systemd to deploy the services"
echo ""
echo "-- execute ansible playbook"
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook stage-machine.yaml --inventory-file=ansible-inventory --ask-pass --ask-sudo-pass
echo ""
echo "-- DONE"