# python-smarttub

This package provides an API for querying and controlling hot tubs using the SmartTub system.

## Installation
```
pip3 install python-smarttub
```

## CLI

### Getting Information
```bash
# Show help
python3 -m smarttub --help

# Show spa status
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD info --status

# Show all information
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD info --all

# Show specific components
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD info --pumps --lights
```

### Controlling Your Spa

#### Setting Temperature
```bash
# Set temperature (Celsius)
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set -t 38.5
```

#### Controlling Pumps
```bash
# Turn pumps on
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --on P1 P2

# Turn pumps off
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --off BLOWER

# Turn all pumps on/off
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --on ALL
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --off ALL

# Available pumps: P1, P2, CP, BLOWER (or JET1, JET2, WATERFALL)
```

#### Controlling Lights
```bash
# Set all lights to a color
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --lights RED

# Set specific lights with NAME:COLOR syntax
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --lights SEATS:BLUE WATERFALL:GREEN

# Set multiple lights to the same color
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --lights ALL:PURPLE

# Turn lights off
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --lights ALL:OFF

# Available light zones: SEATS, WATERFALL, FOOTWELL, EXTERIOR
# Available colors: RED, GREEN, BLUE, WHITE, ORANGE, PURPLE, YELLOW, AQUA, MULTI, OFF
```

#### Using Standard Light Mode
```bash
# Alternative syntax using --light_mode
python3 -m smarttub -u SMARTTUB_EMAIL -p SMARTTUB_PASSWORD set --light_mode HIGH_SPEED_COLOR_WHEEL
```

## API
```
from smarttub import SmartTub

async with aiohttp.ClientSession() as session:
  st = SmartTub(session)
  await st.login(username, password)
  account = await st.get_account()
  spas = await account.get_spas()
  for spa in spas:
    spa.get_status()
    spa.get_pumps()
    spa.get_lights()
    ...
    # See pydoc3 smarttub.api for complete API
```

See also `smarttub/__main__.py` for example usage

## Troubleshooting

If this module is not working with your device, please run the following
command and include the output with your bug report:

```bash
python3 -m smarttub -u YOUR_SMARTTUB_EMAIL -p YOUR_SMARTTUB_PASSWORD -vv info -a
```

## Contributing
```bash
uv sync --extra dev
uv run pre-commit install
```
