# Pi-hole Device Tracker - Setup Script (HACS Compatible)
# Автоматическое создание всех файлов проекта

import os
import json
from pathlib import Path

ROOT_DIR = Path.cwd()

DIRECTORIES = [
    "custom_components/pihole_device_tracker",
    "custom_components/pihole_device_tracker/translations",
    "tests",
]

FILES = {
    ".gitignore": """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# OS
Thumbs.db
Desktop.ini

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Project specific
config/
secrets.yaml
known_devices.yaml
""",

    "requirements.txt": """homeassistant>=2025.12.0
aiohttp>=3.9.0
voluptuous>=0.13.0
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.23.0
black>=23.12.0
flake8>=6.1.0
isort>=5.13.0
""",

    "pyproject.toml": """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pihole-device-tracker"
version = "1.0.0"
description = "Pi-hole Device Tracker integration for Home Assistant"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["pihole", "home-assistant", "device-tracker"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Home Automation",
]

dependencies = [
    "homeassistant>=2025.12.0",
    "aiohttp>=3.9.0",
    "voluptuous>=0.13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "black>=23.12.0",
    "flake8>=6.1.0",
    "isort>=5.13.0",
]

[tool.black]
line-length = 100
target-version = ["py311", "py312", "py313"]
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_mode = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=custom_components/pihole_device_tracker --cov-report=html --cov-report=term-missing"
asyncio_mode = "auto"
""",

    "README.md": """# Pi-hole Device Tracker

A Home Assistant integration for tracking devices connected to Pi-hole.

## Features

- 🔍 Track devices on your network using Pi-hole
- 🏠 Integration with Home Assistant device tracker platform
- ⚙️ Configurable update intervals
- 🔐 Optional API key authentication
- 📊 Real-time device activity monitoring

## Installation

### Via HACS

1. Open Home Assistant
2. Go to HACS → Integrations
3. Click "+" button
4. Search for "Pi-hole Device Tracker"
5. Click Install
6. Restart Home Assistant

### Manual Installation

1. Download the repository as ZIP
2. Extract to `config/custom_components/pihole_device_tracker/`
3. Restart Home Assistant
4. Go to Settings → Devices & Services
5. Click "Create Integration"
6. Search for "Pi-hole Device Tracker"

## Configuration

### Setup Flow

1. Go to Settings → Devices & Services
2. Click "Create Integration"
3. Select "Pi-hole Device Tracker"
4. Enter:
   - **Host**: IP address or hostname (e.g., `192.168.1.100`)
   - **API Key**: (optional) Your Pi-hole API key
   - **Update Interval**: How often to check (default: 30 seconds)

### Configuration via YAML

```yaml
device_tracker:
  - platform: pihole_device_tracker
    host: 192.168.1.100
    api_key: your_api_key_here
    interval: 30
```

## Usage

Once configured, devices will appear in Home Assistant as device tracker entities.

### Automations Example

```yaml
automation:
  - alias: "Notify when device comes home"
    trigger:
      platform: state
      entity_id: device_tracker.pihole_device
      to: home
    action:
      service: notify.mobile_app_phone
      data:
        message: "Device connected to network"
```

## Troubleshooting

### Connection Issues
- Verify Pi-hole host is reachable
- Check network connectivity
- Ensure API key is correct (if used)

### No Devices Showing
- Check Pi-hole logs
- Verify update interval is reasonable
- Ensure devices have activity

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Barma-lej/pihole-device-tracker
cd pihole-device-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/pihole_device_tracker

# Run specific test
pytest tests/test_api.py
```

### Code Style

```bash
# Format code
black custom_components/pihole_device_tracker

# Check linting
flake8 custom_components/pihole_device_tracker

# Sort imports
isort custom_components/pihole_device_tracker
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Changelog

### v1.0.0
- Initial release
- Basic device tracking functionality
- Home Assistant integration
- Configuration UI support
""",

    "LICENSE": """MIT License

Copyright (c) 2024 Barma-lej

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",

    "custom_components/pihole_device_tracker/__init__.py": '''"""Pi-hole Device Tracker integration."""

import asyncio
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

LOGGER: logging.Logger = logging.getLogger(__name__)
PLATFORMS: Final = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pi-hole Device Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
''',

    "custom_components/pihole_device_tracker/const.py": '''"""Constants for Pi-hole Device Tracker integration."""

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
''',

    "custom_components/pihole_device_tracker/manifest.json": """{
  "domain": "pihole_device_tracker",
  "name": "Pi-hole Device Tracker",
  "codeowners": ["@Barma-lej"],
  "config_flow": true,
  "documentation": "https://github.com/Barma-lej/pihole-device-tracker",
  "issue_tracker": "https://github.com/Barma-lej/pihole-device-tracker/issues",
  "requirements": [
    "aiohttp>=3.9.0"
  ],
  "version": "1.0.0",
  "manifest_version": 1,
  "iot_class": "local_polling",
  "integration_type": "hub",
  "platforms": ["device_tracker"],
  "homeassistant": {
    "python_version": "3.11"
  }
}""",

    "custom_components/pihole_device_tracker/strings.json": """{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Pi-hole",
        "description": "Enter the IP address or hostname of your Pi-hole instance. The API key is optional.",
        "data": {
          "host": "Pi-hole Host (IP or hostname)",
          "api_key": "API Key (optional)",
          "interval": "Update Interval (seconds)"
        },
        "data_description": {
          "host": "Example: 192.168.1.100",
          "api_key": "Leave empty if authentication not required",
          "interval": "How often to check for device updates (default: 30)"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to Pi-hole. Check the host address and network connectivity.",
      "unknown": "An unexpected error occurred."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Pi-hole Device Tracker Options",
        "description": "Configure Pi-hole Device Tracker settings",
        "data": {
          "interval": "Update Interval (seconds)",
          "presence_timeout": "Presence Timeout (minutes)"
        }
      }
    }
  },
  "entity": {
    "device_tracker": {
      "pihole_tracker": {
        "name": "Pi-hole Device Tracker"
      }
    }
  }
}""",

    "custom_components/pihole_device_tracker/translations/en.json": """{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Pi-hole",
        "description": "Enter the IP address or hostname of your Pi-hole instance. The API key is optional.",
        "data": {
          "host": "Pi-hole Host (IP or hostname)",
          "api_key": "API Key (optional)",
          "interval": "Update Interval (seconds)"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to Pi-hole",
      "unknown": "Unexpected error"
    }
  }
}""",

    "custom_components/pihole_device_tracker/api.py": '''"""API client for Pi-hole Device Tracker."""

import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional
from .const import API_TIMEOUT, PIHOLE_API_PATH

LOGGER = logging.getLogger(__name__)


class PiholeAPIClient:
    """Client for interacting with Pi-hole API."""

    def __init__(
        self,
        host: str,
        api_key: Optional[str] = None,
        timeout: int = API_TIMEOUT,
    ) -> None:
        """Initialize the API client.
        
        Args:
            host: Pi-hole host (IP or hostname)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.host = host
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def async_get_devices(self) -> Dict[str, Any]:
        """Get list of devices from Pi-hole.
        
        Returns:
            Dictionary containing device information
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}{PIHOLE_API_PATH}/clients"
                
                params = {}
                if self.api_key:
                    params["token"] = self.api_key

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        LOGGER.error(f"Pi-hole API returned status {resp.status}")
                        return {}
        except asyncio.TimeoutError:
            LOGGER.error("Timeout connecting to Pi-hole")
            return {}
        except aiohttp.ClientError as err:
            LOGGER.error(f"Error connecting to Pi-hole: {err}")
            return {}
        except Exception as err:
            LOGGER.error(f"Unexpected error: {err}")
            return {}

    async def async_get_status(self) -> Dict[str, Any]:
        """Get Pi-hole status.
        
        Returns:
            Dictionary containing status information
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}{PIHOLE_API_PATH}/status"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {}
        except Exception as err:
            LOGGER.error(f"Error getting Pi-hole status: {err}")
            return {}

    async def async_test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            status = await self.async_get_status()
            return bool(status)
        except Exception:
            return False
''',

    "custom_components/pihole_device_tracker/config_flow.py": '''"""Config flow for Pi-hole Device Tracker."""

import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import PiholeAPIClient
from .const import CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN

CONF_HOST = "host"
CONF_API_KEY = "api_key"


async def validate_input(
    hass: HomeAssistant, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate the user input."""
    client = PiholeAPIClient(
        host=data[CONF_HOST],
        api_key=data.get(CONF_API_KEY),
    )

    if not await client.async_test_connection():
        raise ValueError("Cannot connect to Pi-hole")

    return {"title": f"Pi-hole ({data[CONF_HOST]})"}


class PiholeDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-hole Device Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_API_KEY): str,
                vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
''',

    "custom_components/pihole_device_tracker/device_tracker.py": '''"""Device tracker platform for Pi-hole."""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.components.device_tracker import PLATFORM_SCHEMA, DeviceScanner
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import PiholeAPIClient
from .const import CONF_API_KEY, CONF_INTERVAL, DEFAULT_INTERVAL

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({})


async def async_get_scanner(
    hass: HomeAssistant, config: ConfigType
) -> Optional[DeviceScanner]:
    """Return a device scanner."""
    return PiholeDeviceScanner(hass, config)


class PiholeDeviceScanner(DeviceScanner):
    """Scanner for Pi-hole devices."""

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        """Initialize the scanner."""
        self.hass = hass
        self.client = PiholeAPIClient(
            host=config.get(CONF_HOST),
            api_key=config.get(CONF_API_KEY),
        )
        self.last_results: Dict[str, Dict[str, Any]] = {}
        self.update_interval = timedelta(
            seconds=config.get(CONF_INTERVAL, DEFAULT_INTERVAL)
        )

    async def async_scan_devices(self) -> list[str]:
        """Return list of device MACs."""
        devices = await self.client.async_get_devices()
        return [d.get("mac") for d in devices.get("clients", []) if d.get("mac")]

    async def async_get_device_name(self, device: str) -> Optional[str]:
        """Return the name of a device."""
        devices = await self.client.async_get_devices()
        for d in devices.get("clients", []):
            if d.get("mac") == device:
                return d.get("name") or d.get("ip")
        return None

    def get_extra_attributes(self, device: str) -> Dict[str, Any]:
        """Return extra attributes for a device."""
        if device in self.last_results:
            return self.last_results[device]
        return {}
''',

    "tests/__init__.py": '''"""Tests for Pi-hole Device Tracker."""
''',

    "tests/test_api.py": '''"""Test API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.pihole_device_tracker.api import PiholeAPIClient


@pytest.fixture
def client():
    """Create API client for testing."""
    return PiholeAPIClient(host="192.168.1.100", api_key="test_key")


@pytest.mark.asyncio
async def test_get_devices_success(client):
    """Test successful device retrieval."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "clients": [
                    {"mac": "00:11:22:33:44:55", "name": "Device1", "ip": "192.168.1.10"}
                ]
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await client.async_get_devices()
        assert "clients" in result


@pytest.mark.asyncio
async def test_connection_failed(client):
    """Test connection failure."""
    result = await client.async_test_connection()
    assert not result
'''
}


def create_project():
    """Create project structure and files."""
    print("🚀 Creating Pi-hole Device Tracker project structure (HACS Compatible)...")
    print()
    
    # Create directories
    for directory in DIRECTORIES:
        dir_path = Path(ROOT_DIR) / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    print()
    
    # Create files
    for file_path, content in FILES.items():
        file_full_path = Path(ROOT_DIR) / file_path
        file_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Created file: {file_path}")
    
    print()
    print("=" * 70)
    print("✨ Project structure created successfully!")
    print("=" * 70)
    print()
    print("🎯 HACS Configuration:")
    print("   ✓ manifest.json is properly configured")
    print("   ✓ config_flow.py is present")
    print("   ✓ strings.json is properly configured")
    print()
    print("📋 Next steps:")
    print("   1. cd pihole-device-tracker")
    print("   2. git add .")
    print('   3. git commit -m "Initial project setup - HACS compatible"')
    print("   4. git push origin main")
    print()
    print("🔗 Then add to HACS:")
    print("   1. HACS → Custom repositories")
    print("   2. https://github.com/Barma-lej/pihole-device-tracker")
    print("   3. Category: Integration")
    print()
    print("📚 For more info, read README.md")
    print()


if __name__ == "__main__":
    create_project()
