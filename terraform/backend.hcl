# Cloud.ru OBS backend for Terraform state
bucket  = "telegram-ai-bot-tfstate"
key     = "terraform/state"
region  = "ru-moscow-1"
endpoint = "https://obs.ru-moscow-1.hc.sbercloud.ru"

# Required flags for Cloud.ru OBS compatibility
skip_credentials_validation = true
skip_region_validation      = true
skip_requesting_account_id  = true

# TEMPORARY: Public access for testing - WILL BE REMOVED AFTER TESTING
# TODO: Replace with proper service account credentials
access_key = "1f7856ce78bad494d2c35ac6a8637421"
secret_key = "aed6b811cc26d4c7a431e6e74a82c263"
