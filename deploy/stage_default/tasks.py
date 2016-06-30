#!/bin/python3
"""
python invoke task to deploy a server using the staging template. Before using, install invoke in your python
environment using pip:

    pip3 install invoke

"""
from invoke import task
import os

ANSIBLE_INVENTORY = "staging_inventory"


@task
def remove_ansible_inventory(ctx):
    """
    remove the generated Ansible inventory file if existing
    """
    if os.path.exists(ANSIBLE_INVENTORY):
        try:
            os.remove(ANSIBLE_INVENTORY)

        except Exception as ex:
            print("WARNING: unable to remove the generated ansible inventory file (%s)" % ex)


@task(pre=[remove_ansible_inventory])
def create_ansible_inventory(ctx, hostname, username=None, password=None):
    """
    generate an Ansible inventory file
    """
    inventory_file_content = "[staging]\n"

    inventory_file_content += "%s" % hostname
    if username:
        inventory_file_content += "   ansible_ssh_user=%s" % username
    if password:
        inventory_file_content += "   ansible_ssh_pass=%s" % password
        inventory_file_content += "   ansible_become_pass=%s" % password

    inventory_file_content += "\n"
    inventory_file_content += "\n[defaults]\n"
    inventory_file_content += "host_key_checking=False\n"

    # write to file
    with open(ANSIBLE_INVENTORY, "w") as f:
        f.write(inventory_file_content)


@task(
    help={
        "hostname": "Hostname or IP where the Product Database should be deployed",
        "username": "username for the Ansible SSH connection",
        "password": "password for the SSH and SUDO user"
    },
    post=[remove_ansible_inventory]
)
def deploy(ctx, hostname, username, password=None):
    """
    deploy the product database on the specified server using Ansible
    """
    # prompt for user and
    print("----")
    print("Stage the latest version of the product database on '%s'\n" % hostname)
    print("Please Note: The ansible playbook expects a server running Ubuntu 16.04 with python 2 installed.")
    print("If you need LDAP authentication, please add the LDAP configuration parameters to your "
          "stage_machine.yaml file")
    print("")

    continue_execution = input("Continue with the execution? [Y/n]")
    if continue_execution == "":
        continue_execution = "Y"

    if continue_execution.lower() == "y":
        create_ansible_inventory(ctx, hostname=hostname, username=username, password=password)
        # run the Ansible playbook
        ctx.run(
            "ansible-playbook stage-machine.yaml --inventory-file=%s" % ANSIBLE_INVENTORY,
            env={
                "ANSIBLE_HOST_KEY_CHECKING": "False"
            }
        )
        print("----------\ndeployment process completed. Check for errors in the output above.\n")

    elif continue_execution.lower() == "n":
        print("okay, skip deployment...")

    else:
        print("invalid response, process terminated")


@task(
    help={
        "username": "username for the Ansible SSH connection",
        "password": "password for the SSH and SUDO user"
    },
    post=[remove_ansible_inventory]
)
def deploy_local(ctx, username, password=None):
    """
    deploy the product database on localhost (please ensure that Ansible is installed)
    """
    deploy(ctx, hostname="127.0.0.1", username=username, password=password)
