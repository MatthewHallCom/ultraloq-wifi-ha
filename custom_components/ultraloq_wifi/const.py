"""Constants for the Ultraloq Wifi integration."""

DOMAIN = "ultraloq_wifi"

# Configuration flow
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ADDRESS_ID = "address_id"

# API constants
USER_AGENT = "U home/3.2.9.2 (Linux; U; Android 12; Android SDK built for arm64 Build/SE1A.220621.001)"
TOKEN_URL = "https://uemc.u-tec.com/app/token"
LOGIN_URL = "https://cloud.u-tec.com/app/user/login"
ADDRESS_URL = "https://cloud.u-tec.com/app/address"
DEVICE_LIST_URL = "https://cloud.u-tec.com/app/device/list/address"
DEVICE_STATUS_URL = "https://cloud.u-tec.com/app/device/status"
DEVICE_TOGGLE_URL = "https://cloud.u-tec.com/app/device/lock/logs/add"
DEVICE_ONLINE_CHECK_URL = "https://cloud.u-tec.com/app/device/lock/share/get/isopen"

# App credentials for token request
APP_ID = "13ca0de1e6054747c44665ae13e36c2c"
CLIENT_ID = "1375ac0809878483ee236497d57f371f"
UUID = "77b7de5d1a5efd83"
VERSION = "3.2"
TIMEZONE = "-8"

# Default values
DEFAULT_NAME = "Ultraloq Wifi"
DEFAULT_TIMEOUT = 30