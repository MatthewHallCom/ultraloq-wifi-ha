# Testing the Ultraloq Wifi Integration

This directory contains comprehensive tests for all API endpoints in the Ultraloq Wifi integration.

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Add your credentials to `.env`:**
   ```env
   ULTRALOQ_EMAIL=your-email@example.com
   ULTRALOQ_PASSWORD=your-password
   ```

## Running Tests

### Option 1: Quick Manual Test
Run the simple test script to verify all endpoints:
```bash
python tests/run_tests.py
```

### Option 2: Full Pytest Suite
Run the comprehensive test suite:
```bash
pytest tests/test_api.py -v
```

### Option 3: With Coverage
Run tests with coverage reporting:
```bash
pytest tests/test_api.py --cov=custom_components.ultraloq_wifi --cov-report=html
```

## Test Coverage

The tests cover all major API endpoints:

### ✅ Authentication Tests
- `test_get_api_token()` - Token endpoint
- `test_authenticate_success()` - Login flow
- `test_authenticate_invalid_credentials()` - Error handling
- `test_authenticate_empty_credentials()` - Input validation

### ✅ Address Tests  
- `test_get_addresses()` - Address listing endpoint

### ✅ Device Tests
- `test_get_devices()` - Device listing endpoint
- `test_get_locks()` - U-Bolt filtering

### ✅ Lock Control Tests
- `test_get_lock_status()` - Status endpoint
- `test_toggle_lock()` - Lock/unlock endpoint

### ✅ Error Handling Tests
- `test_unauthenticated_requests()` - Auth validation
- `test_invalid_device_uuid()` - UUID validation  
- `test_invalid_address_id()` - Address validation

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ULTRALOQ_EMAIL` | Yes | Your Ultraloq account email |
| `ULTRALOQ_PASSWORD` | Yes | Your Ultraloq account password |
| `ULTRALOQ_TEST_UUID` | No | Specific lock UUID for testing |
| `ULTRALOQ_ADDRESS_ID` | No | Specific address ID for testing |

## Safety Notes

⚠️ **Important:** These are integration tests that connect to real Ultraloq servers and may control actual locks. The toggle lock test will actually lock/unlock your door.

- Tests run against live API endpoints
- Lock toggle tests will physically operate your lock
- Use a test environment or be prepared for actual lock operations
- Tests include delays to allow lock mechanisms to respond

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Pytest configuration
├── test_api.py              # Main API integration tests
├── run_tests.py             # Simple manual test runner
└── README.md                # This file
```

## Troubleshooting

**Authentication Errors:**
- Verify credentials in `.env` file
- Check that your Ultraloq account is active
- Ensure you have locks associated with your account

**Network Errors:**
- Check internet connectivity
- Verify Ultraloq servers are accessible
- Consider firewall/proxy issues

**No Devices Found:**
- Ensure your account has registered U-Bolt locks
- Check that locks are online and accessible
- Verify address configuration in Ultraloq app