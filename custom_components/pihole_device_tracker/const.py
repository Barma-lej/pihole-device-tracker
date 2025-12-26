"""Constants for Pi-hole Device Tracker integration."""

DOMAIN = "pihole_device_tracker"
PLATFORM = "device_tracker"

# Configuration constants
CONF_INTERVAL = "interval"
DEFAULT_INTERVAL = 30  # seconds

# API constants
API_TIMEOUT = 10
PIHOLE_API_PATH = "/api"

# Entity attributes
ATTR_DEVICE_NAME = "name"
ATTR_DEVICE_MAC = "mac"
ATTR_DEVICE_IP = "ip"
ATTR_DEVICE_ACTIVITY = "activity"
ATTR_DEVICE_TYPE = "device_type"

# Device states
STATE_HOME = "home"
STATE_NOT_HOME = "not_home"

# Update intervals (in seconds)
UPDATE_INTERVAL = 30
SCAN_INTERVAL = 60
