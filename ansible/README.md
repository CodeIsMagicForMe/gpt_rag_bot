# Infrastructure automation

This directory contains the automation required to provision and configure VPN nodes hosted at ishosting.  The playbook deploys VPN services (WireGuard, OpenVPN, AmneziaWG), SmartDNS, security hardening, monitoring, journald backups, and the application stack (bot, billing, provisioner).

## Usage

1. Install the required Ansible collections:

   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

2. Adjust variables in `group_vars/all.yml` to match your environment:
   - Set `environment` to `dev`, `stage`, or `prod`.
   - Fill in `yandex_lockbox_secret_ids` with the Lockbox secret IDs for each environment.  Each secret must contain entries for `admin_ssh_keys`, `admin_totp_secret`, `bot_token`, `billing_database_url`, `provisioner_endpoint`, `telegram_bot_token`, and `telegram_chat_id`.
   - Provide non-secret defaults (VPN peers, container images, etc.).

3. Update the inventory at `inventory/hosts.yml` with the actual public IPv4 addresses of your ishosting Medium servers (or use the Terraform-generated inventory at `inventory/generated_hosts.yml`).

4. Export a Yandex Cloud token or service-account key so that the `community.yandex_cloud` collection can retrieve secrets:

   ```bash
   export YC_TOKEN="$(yc iam create-token)"
   # or
   export YC_SERVICE_ACCOUNT_KEY_FILE=/path/to/key.json
   ```

5. Run the playbook:

   ```bash
   ansible-playbook -i inventory/hosts.yml site.yml -e environment=prod
   ```

The playbook is idempotent and can be re-run at any time to apply configuration drift corrections.
