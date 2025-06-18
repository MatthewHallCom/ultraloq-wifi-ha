# Ultraloq Wifi for Home Assistant

A Home Assistant custom component to integrate Ultraloq Wifi smart locks.

## Features

- Control Ultraloq Wifi smart locks from Home Assistant
- Lock/unlock functionality
- Battery status monitoring
- Real-time status updates

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS
3. Install the "Ultraloq Wifi for Home Assistant" integration
4. Restart Home Assistant
5. Go to Configuration > Integrations and add the Ultraloq Wifi integration

### Manual Installation

1. Copy the `custom_components/ultraloq_wifi` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations and add the Ultraloq Wifi integration

## Configuration

The integration uses the config flow for setup. You'll need:

- Your Ultraloq account username
- Your Ultraloq account password

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/matt/ultraloq-wifi-ha).