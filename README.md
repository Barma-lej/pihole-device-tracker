# Pi-hole Device Tracker

[![HACS][hacs-image]][hacs-url]
[![Buy Me A Coffee][buymeacoffee-image]][buymeacoffee-url]
<!-- ![Latest release][latest-url] -->
<!-- ![All releases][downloads] -->
<!-- ![Latest release][downloads_latest] -->

A Home Assistant integration for tracking devices on your network using Pi-hole v6.0+.

## Features

- 🔍 Track devices based on DNS activity in Pi-hole
- 🏠 Integration with Home Assistant device tracker platform
- ⚙️ Configurable update intervals (minimum 5 seconds)
- 🔐 Password authentication for Pi-hole web interface
- 📊 Rich device information (name, IP, MAC vendor, last query time)
- 🌐 Multi-language support (EN, RU, DE)

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
5. Click "Add Integration"
6. Search for "Pi-hole Device Tracker"

## Configuration

### Setup Flow

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Select "Pi-hole Device Tracker"
4. Enter:
   - **Host**: Pi-hole IP or hostname (e.g., `192.168.1.100` or `pi.hole`)
   - **Password**: Web interface password (leave empty if no password)
   - **Poll Interval**: How often to check Pi-hole (default: 30 seconds, min: 5)
   - **Consider Away After**: Time without DNS activity before marking device as away (default: 900 seconds = 15 minutes)

## Usage

Once configured, devices will appear in Home Assistant as device tracker entities.

### Entity IDs

Entity IDs are generated based on device name + last 4 MAC characters + "pihole":

- `device_tracker.iphone_a1b2_pihole`
- `device_tracker.macbook_c3d4_pihole`
- `device_tracker.192_168_1_50_pihole` (if no name available)

### Attributes

Each tracker includes additional attributes:

- `last_query`: Timestamp of last DNS query
- `last_query_seconds_ago`: Seconds since last activity
- `first_seen`: When device was first seen
- `num_queries`: Total number of queries
- `mac_vendor`: Device manufacturer
- `ips`: IP addresses
- `name`: Device name from Pi-hole
- `dhcp_expires`: DHCP lease expiration
- `interface`: Network interface

### Automations Example

```yaml
automation:
  - alias: "Notify when device comes home"
    trigger:
      platform: state
      entity_id: device_tracker.iphone_a1b2_pihole
      to: "home"
    action:
      service: notify.mobile_app_phone
      data:
        message: "Device connected to network"

  - alias: "Notify when device leaves"
    trigger:
      platform: state
      entity_id: device_tracker.iphone_a1b2_pihole
      to: "not_home"
    action:
      service: notify.mobile_app_phone
      data:
        message: "Device left the network"
```

## Troubleshooting

### Connection Issues

- Verify Pi-hole host is reachable: `ping <host>`
- Check network connectivity between Home Assistant and Pi-hole
- Ensure password is correct (if configured)
- Check Pi-hole API is enabled (Settings → API → Web server API)

### No Devices Showing

- Devices must have DNS activity to appear
- Check Pi-hole settings → Network for device list
- Verify update interval is reasonable
- Check Home Assistant logs: Settings → System → Logs

### Devices Not Updating

- Increase poll interval if network is slow
- Check Pi-hole is not overloaded
- Verify Consider Away After setting is appropriate

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Barma-lej/pihole-device-tracker
cd pihole-device-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

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
pytest tests/test_pihole_connection.py
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

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub: https://github.com/Barma-lej/pihole-device-tracker/issues

**💡 Tip:** If you like this project just buy me a cup of ☕️ or 🥤:

[![Buy Me A Coffee][buymeacoffee-img]][buymeacoffee-url]

<!-- Badges -->

[hacs-url]: https://github.com/hacs/integration
[hacs-image]: https://img.shields.io/badge/hacs-default-orange.svg?style=flat-square
[buymeacoffee-url]: https://www.buymeacoffee.com/barma
[buymeacoffee-image]: https://img.shields.io/badge/donate-Coffee-ff813f.svg
<!-- [latest-url]: https://img.shields.io/github/v/release/Barma-lej/pihole-device-tracker
[downloads]: https://img.shields.io/github/downloads/Barma-lej/pihole-device-tracker/total
[downloads_latest]: https://img.shields.io/github/downloads/Barma-lej/pihole-device-tracker/latest/total -->

<!-- References -->

[buymeacoffee-img]: https://www.buymeacoffee.com/assets/img/custom_images/white_img.png
