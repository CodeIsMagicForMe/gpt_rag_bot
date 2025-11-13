# Infrastructure automation

This directory contains the automation required to provision and configure VPN nodes hosted at ishosting.  The playbook deploys VPN services (WireGuard, OpenVPN, AmneziaWG), SmartDNS, security hardening, monitoring, journald backups, and the application stack (bot, billing, provisioner).

## Usage

1. Install the required Ansible collections:

   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

2. Adjust variables in `group_vars/all.yml` to match your environment (SSH keys, VPN peers, Telegram tokens, Rclone credentials, container images, etc.).

3. Update the inventory at `inventory/hosts.yml` with the actual public IPv4 addresses of your ishosting Medium servers.

4. Run the playbook:

   ```bash
   ansible-playbook -i inventory/hosts.yml site.yml
   ```

The playbook is idempotent and can be re-run at any time to apply configuration drift corrections.
