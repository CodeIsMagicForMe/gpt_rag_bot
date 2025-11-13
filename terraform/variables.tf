variable "ishosting_api_base" {
  description = "Base URL for the ishosting API"
  type        = string
  default     = "https://api.ishosting.com/client/v2"
}

variable "ishosting_api_token" {
  description = "API token for authenticating against the ishosting API"
  type        = string
  sensitive   = true
}

variable "servers" {
  description = "List of server definitions to create"
  type = list(object({
    hostname    = string
    location    = string
    plan        = string
    image       = string
    ipv4_count  = number
    ssh_keys    = list(string)
    user_data   = optional(string)
    tags        = optional(list(string))
  }))
  default = [
    {
      hostname   = "vpn-01"
      location   = "nl1"
      plan       = "medium"
      image      = "ubuntu-22-04-x64"
      ipv4_count = 3
      ssh_keys   = []
      user_data  = null
      tags       = ["vpn", "production"]
    },
    {
      hostname   = "vpn-02"
      location   = "nl1"
      plan       = "medium"
      image      = "ubuntu-22-04-x64"
      ipv4_count = 3
      ssh_keys   = []
      user_data  = null
      tags       = ["vpn", "production"]
    },
    {
      hostname   = "vpn-03"
      location   = "nl1"
      plan       = "medium"
      image      = "ubuntu-22-04-x64"
      ipv4_count = 3
      ssh_keys   = []
      user_data  = null
      tags       = ["vpn", "production"]
    }
  ]
}

variable "ansible_inventory_path" {
  description = "Path on the local filesystem where the Ansible inventory file should be generated"
  type        = string
  default     = "../ansible/inventory/generated_hosts.yml"
}
