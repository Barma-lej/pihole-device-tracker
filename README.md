# Pi-hole Device Tracker

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
