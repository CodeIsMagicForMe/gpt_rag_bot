locals {
  lockbox_secret_id = local.selected_environment.lockbox_secret_id
}

data "yandex_lockbox_secret_version" "selected" {
  count     = length(trimspace(local.lockbox_secret_id)) > 0 ? 1 : 0
  secret_id = local.lockbox_secret_id
}

locals {
  lockbox_entries = length(data.yandex_lockbox_secret_version.selected) > 0 ? {
    for entry in data.yandex_lockbox_secret_version.selected[0].entries :
    entry.key => coalesce(entry.text_value, entry.binary_value, "")
  } : {}
  raw_ishosting_api_token = length(trimspace(var.ishosting_api_token_override)) > 0
    ? var.ishosting_api_token_override
    : lookup(local.lockbox_entries, "ishosting_api_token", "")
  ishosting_api_token = trimspace(local.raw_ishosting_api_token)
}

resource "null_resource" "validate_lockbox" {
  count = 1

  lifecycle {
    precondition {
      condition     = local.ishosting_api_token != ""
      error_message = "Provide ishosting_api_token via Lockbox secret or set ishosting_api_token_override"
    }
  }
}
