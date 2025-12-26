"""Constants for Pi-hole Device Tracker integration."""

DOMAIN = "pihole_device_tracker"

# Configuration
CONF_HOST = "host"
CONF_PASSWORD = "password"
CONF_POLL_INTERVAL = "poll_interval"
CONF_CONSIDER_AWAY = "consider_away"

# Defaults
DEFAULT_POLL_INTERVAL = 30  # seconds
DEFAULT_CONSIDER_AWAY = 900  # 15 minutes in seconds
DEFAULT_TIMEOUT = 10  # seconds

# API
PIHOLE_API_BASE = "/api"
PIHOLE_DEVICES_ENDPOINT = "/api/network/devices"
PIHOLE_DHCP_ENDPOINT = "/api/dhcp/leases"
PIHOLE_AUTH_ENDPOINT = "/api/auth"

# Attributes
ATTR_MAC = "mac"
ATTR_IP = "ip"
ATTR_HOSTNAME = "hostname"
ATTR_LAST_QUERY = "last_query"
ATTR_FIRST_SEEN = "first_seen"

# Platforms
PLATFORMS = ["device_tracker", "sensor"]