# Terraform provisioning for ishosting Medium nodes

This module uses the generic REST API provider to communicate with the ishosting control panel API.  It creates Medium VPS instances with 3 dedicated IPv4 addresses by default and renders an Ansible inventory that is consumed by the playbook in `../ansible`.

> **Note**
> The exact API endpoints, field names, and authentication headers exposed by ishosting may evolve.  Review the `restapi_object` configuration and adjust the JSON payload to match the current ishosting API schema before running `terraform apply`.

## Prerequisites

- Terraform >= 1.5
- An ishosting API token with permissions to manage servers and IPv4 addresses
- The `restapi` provider (`terraform init` downloads it automatically)

## Usage

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in the sensitive values:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Review `variables.tf` and tailor the `servers` definition (hostnames, locations, SSH keys, IPv4 counts).

3. Initialize and apply:

   ```bash
   terraform init
   terraform apply
   ```

4. After a successful apply the generated Ansible inventory is written to `../ansible/inventory/generated_hosts.yml` and can be used directly with `ansible-playbook`.

Destroy the infrastructure when it is no longer needed:

```bash
terraform destroy
```
