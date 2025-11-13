variable "environment" {
  description = "Deployment environment (dev, stage, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Environment must be one of dev, stage, prod"
  }
}

variable "environments" {
  description = "Environment specific configuration (servers + Lockbox secret id)"
  type = map(object({
    lockbox_secret_id = string
    servers = list(object({
      hostname    = string
      location    = string
      plan        = string
      image       = string
      ipv4_count  = number
      ssh_keys    = list(string)
      user_data   = optional(string)
      tags        = optional(list(string))
    }))
  }))
  default = {
    dev = {
      lockbox_secret_id = ""
      servers = []
    }
    stage = {
      lockbox_secret_id = ""
      servers = []
    }
    prod = {
      lockbox_secret_id = ""
      servers = []
    }
  }
}

variable "ishosting_api_base" {
  description = "Base URL for the ishosting API"
  type        = string
  default     = "https://api.ishosting.com/client/v2"
}

variable "ishosting_api_token_override" {
  description = "Optional override for the ishosting API token (bypasses Lockbox)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "yandex_token" {
  description = "OAuth token for Yandex Cloud (can also be supplied via YC_TOKEN env var)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "yandex_service_account_key_file" {
  description = "Path to a service account key JSON file for Yandex Cloud (optional if token is used)"
  type        = string
  default     = ""
}

variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  default     = ""
}

variable "yandex_folder_id" {
  description = "Yandex Cloud Folder ID that stores Lockbox secrets"
  type        = string
  default     = ""
}

variable "ansible_inventory_path" {
  description = "Path on the local filesystem where the Ansible inventory file should be generated"
  type        = string
  default     = "../ansible/inventory/generated_hosts.yml"
}
