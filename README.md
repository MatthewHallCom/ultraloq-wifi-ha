# Ultraloq Wifi for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom component to integrate Ultraloq Wifi smart locks. This has only been tested with the ULTRALOQ U-Bolt Smart Lock + Brdige WiFi Adapter.

**Note: Right now this only reports the lock status, we have not been able to get locking & unlocking to work yet**

## Installation

### HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots menu > Custom repositories
   - Add `https://github.com/MatthewHallCom/ultraloq-wifi-ha` as Integration
3. Find and install "Ultraloq Wifi for Home Assistant"
4. Restart Home Assistant
5. Add the integration through Configuration > Integrations

### Manual Installation

1. Copy `custom_components/ultraloq_wifi/` to your `<config>/custom_components/` directory
2. Restart Home Assistant
3. Add the integration through Configuration > Integrations

## Configuration

Configure through the Home Assistant UI:

1. Go to Configuration > Integrations
2. Click "Add Integration"
3. Search for "Ultraloq Wifi"
4. Enter your Ultraloq account credentials

## Features

- Lock/unlock control
- Battery status monitoring
- Real-time status updates
- Multiple lock support

## Development

This component is in active development. Features and API may change.

## License

This project is licensed under the MIT License.
