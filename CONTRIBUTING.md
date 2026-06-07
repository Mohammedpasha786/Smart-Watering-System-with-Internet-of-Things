# Contributing to Smart Watering System

Thank you for your interest in contributing! Please follow these guidelines.

## Development Setup

```bash
git clone https://github.com/your-username/smart-watering-iot.git
cd smart-watering-iot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install pytest flake8
```

## Branch Naming

- `feature/your-feature-name`
- `fix/bug-description`
- `docs/update-description`

## Before Submitting a PR

1. Run tests: `pytest tests/ -v`
2. Run linter: `flake8 src/python/ tests/ --max-line-length=110`
3. Add tests for new features
4. Update README.md if adding new capabilities

## Areas to Contribute

- Additional sensor drivers (EC sensor, flow meter)
- LSTM model for seasonal forecasting
- Mobile-responsive dashboard improvements
- LoRa/MQTT long-range communication support
- Drone imaging integration module

## Code Style

- Follow PEP 8 (max line length: 110)
- Add docstrings to all public functions
- Use type hints for function signatures
