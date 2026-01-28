# Ansible for BookRide

This folder holds Ansible config, inventory, and playbooks for managing Linux hosts
related to the project. If you are on Windows, run Ansible from WSL (Ubuntu) or a
Linux VM and target your Linux machines over SSH.

## Quick start
1) Install Ansible in WSL or Linux:
   - Ubuntu/Debian: `sudo apt update && sudo apt install -y ansible`
2) Edit the inventory to point at your Linux host(s):
   - `ops/ansible/inventories/dev/hosts.ini`
3) Set defaults for your environment:
   - `ops/ansible/inventories/dev/group_vars/all.yml`
4) Test connectivity:
   - `ansible-playbook -i inventories/dev/hosts.ini playbooks/ping.yml`
5) Provision Docker and deploy the stack:
   - `ansible-playbook -i inventories/dev/hosts.ini playbooks/site.yml`

## Layout
- `ansible.cfg` config for this repo
- `inventories/` environment-specific host lists
- `playbooks/` entry points for running tasks
- `roles/` reusable role logic (Docker install + app deploy)

## Notes
- SSH access to targets is required.
- If you need Windows targets later, we can add WinRM inventory settings.
- The deploy role syncs the repo contents to `/opt/bookride` and runs `docker compose up -d --build`.

## Ansible start
'''
cd ops/ansible
ansible-playbook -i inventories/dev/hosts.ini playbooks/site.yml --ask-become-pass
'''
