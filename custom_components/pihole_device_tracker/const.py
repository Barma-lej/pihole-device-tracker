"""Constants for Pi-hole Device Tracker integration."""

DOMAIN = "pihole_device_tracker"

CONF_AWAY_TIME = "away_time"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SSH_HOST = "ssh_host"
CONF_SSH_PORT = "ssh_port"
CONF_SSH_USERNAME = "ssh_username"
CONF_SSH_PASSWORD = "ssh_password"
CONF_SSH_KEY_PATH = "ssh_key_path"

DEFAULT_HOST = "http://pi.hole"
DEFAULT_PASSWORD = ""
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_AWAY_TIME = 900

DEFAULT_SSH_PORT = 22
DEFAULT_SSH_USERNAME = "pi"

ATTR_INTERFACE = "interface"
ATTR_FIRST_SEEN = "first_seen"
ATTR_LAST_QUERY = "last_query"
ATTR_NUM_QUERIES = "num_queries"
ATTR_MAC_VENDOR = "mac_vendor"
ATTR_IPS = "ips"
ATTR_NAME = "name"
ATTR_DHCP_EXPIRES = "dhcp_expires"
ATTR_ARP_IP = "arp_ip"

AUTH_ENDPOINT = "/api/auth"
LEASES_ENDPOINT = "/api/dhcp/leases"
DEVICES_ENDPOINT = "/api/network/devices?max_devices=999&max_addresses=24"
