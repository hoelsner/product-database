#!/usr/bin/env bash
echo ""
echo "Start staging on the <hostname> machine"
echo ""
echo "-- execute ansible playbook"
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook stage-machine.yaml --inventory-file=ansible-inventory --ask-pass
echo ""
echo "-- DONE"