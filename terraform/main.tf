locals {
  servers = { for server in var.servers : server.hostname => server }
}

provider "restapi" {
  uri                  = var.ishosting_api_base
  write_returns_object = true
  headers = {
    Authorization = "Bearer ${var.ishosting_api_token}"
    Content-Type  = "application/json"
  }
}

resource "restapi_object" "server" {
  for_each     = local.servers
  path         = "/servers"
  id_attribute = "id"

  data_json = jsonencode(merge({
    hostname   = each.value.hostname
    plan       = each.value.plan
    location   = each.value.location
    image      = each.value.image
    ipv4_count = each.value.ipv4_count
    ssh_keys   = each.value.ssh_keys
  }, each.value.user_data != null ? { user_data = each.value.user_data } : {}, each.value.tags != null ? { tags = each.value.tags } : {}))
}

locals {
  server_inventory = {
    for hostname, server in restapi_object.server :
    hostname => {
      id            = server.id
      location      = local.servers[hostname].location
      plan          = local.servers[hostname].plan
      ipv4_addresses = try(server.api_data["ipv4"], server.api_data["ip_addresses"], [])
      primary_ipv4  = coalesce(
        try(server.api_data["primary_ipv4"], null),
        try(server.api_data["ipv4"][0], null),
        try(server.api_data["ip_addresses"][0], null),
        ""
      )
    }
  }
}

resource "local_file" "ansible_inventory" {
  content  = templatefile("${path.module}/templates/ansible_hosts.tftpl", { servers = local.server_inventory })
  filename = var.ansible_inventory_path
}
