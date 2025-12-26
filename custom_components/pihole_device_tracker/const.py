"""Constants for Pi-hole Device Tracker integration."""

# Domain
DOMAIN = "pihole_device_tracker"

# Configuration
CONF_HOST = "host"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_TIMEOUT = 10  # seconds

# Attributes
ATTR_DEVICE_NAME = "device_name"
ATTR_DEVICE_IP = "device_ip"
ATTR_LAST_SEEN = "last_seen"

# Platforms
PLATFORMS = ["device_tracker"]

# API Endpoints
API_TIMEOUT = 10
PIHOLE_API_PATH = "/api"  # Pi-hole v6.0+ API path
