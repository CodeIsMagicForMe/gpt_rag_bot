# Terraform provisioning for ishosting Medium nodes

This module provisions VPN nodes on ishosting and renders an environment-aware Ansible inventory that feeds the playbooks in `../ansible`.  Each environment (dev/stage/prod) has its own server list and a dedicated secret in Yandex Lockbox containing the tokens required to talk to the ishosting API.

> **Note**
> The ishosting REST API is not formally versioned.  Review the payload in `restapi_object.server` before applying changes if the upstream API schema changes.

## Prerequisites

- Terraform >= 1.5
- Access to Yandex Cloud with permissions to read Lockbox secrets (`yandex.lockbox.viewer`)
- An ishosting API token stored in Yandex Lockbox (entry key `ishosting_api_token`)
- The following providers (downloaded automatically on `terraform init`): `yandex`, `restapi`, `local`, `template`, `null`

## Configuration workflow

1. **Prepare Lockbox secrets**

   Create three Lockbox secrets (dev/stage/prod).  Each secret must include at least the key `ishosting_api_token`.  Additional entries can be added for Ansible (see `ansible/roles/secrets`).

2. **Copy the example variables**

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

   Set the Cloud/Folder identifiers, authentication method (OAuth token or service-account key), and the Lockbox secret IDs.  Populate the `servers` list for every environment that should be provisioned.  You can override the token with `ishosting_api_token_override` during development without touching Lockbox.

3. **Select an environment**

   The `environment` variable defaults to `dev`.  Switch environments either by editing `terraform.tfvars` or by using `TF_VAR_environment=stage terraform apply`.  Each environment is isolated in its own Terraform state and Lockbox secret.

4. **Initialize and apply**

   ```bash
   terraform init
   terraform apply
   ```

   After a successful run the rendered inventory is available at `../ansible/inventory/generated_hosts.yml` and includes the selected environment name under each host.

Destroy the infrastructure when it is no longer needed:

```bash
terraform destroy
```
