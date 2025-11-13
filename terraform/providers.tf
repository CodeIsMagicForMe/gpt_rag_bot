provider "yandex" {
  token                  = trimspace(var.yandex_token) != "" ? trimspace(var.yandex_token) : null
  service_account_key_file = trimspace(var.yandex_service_account_key_file) != "" ? var.yandex_service_account_key_file : null
  cloud_id               = trimspace(var.yandex_cloud_id) != "" ? var.yandex_cloud_id : null
  folder_id              = trimspace(var.yandex_folder_id) != "" ? var.yandex_folder_id : null
}
