# DC Metro Status Plugin

Display real-time Washington DC Metro train arrivals on an LED matrix. The plugin fetches WMATA station predictions, shows upcoming trains for a configured reference station, and vertically scrolls the arrival list (with page numbers when applicable).

**Key features**
- Live WMATA arrivals (StationPrediction API)
- Line-colored text for official line colors (RD, BL, SV, OR, GR, YL)
- Vertical scrolling of all available predictions; always displays at least 3 rows (pads with "NO DATA")
- Configurable `reference_station`, `refresh_interval`, and `page_display_time`

## Installation

1. Obtain a WMATA API key at https://developer.wmata.com/ (required).
2. Install the plugin via your LEDMatrix plugin mechanism or copy this directory into your plugin-repos.

## Configuration

This project includes a JSON schema at [config_schema.json](config_schema.json) describing the supported configuration. The important properties are:

- `enabled` (boolean, default: `true`) — Enable or disable the plugin.
- `wmata_api_key` (string, required) — Your WMATA API key (marked secret in the schema).
- `reference_station` (string, required) — Reference station name (e.g. "Metro Center").
- `refresh_interval` (integer, default: `30`) — How often (seconds) to poll the WMATA API. Valid range: 10–300.
- `page_display_time` (integer, default: `10`) — How long (seconds) to display each page of results. Valid range: 5–60.

Required fields per schema: `enabled`, `wmata_api_key`, and `reference_station`.

Example `config.json`:

```json
{
  "enabled": true,
  "wmata_api_key": "YOUR_API_KEY",
  "reference_station": "Metro Center",
  "refresh_interval": 30,
  "page_display_time": 10
}
```

For security, keep secrets separate (e.g. `config-secret.json`) and do not commit API keys to source control.

## Behavior & Display

- The plugin queries WMATA's StationPrediction endpoint and parses the `Trains` list.
- It shows all returned trains in a vertical list and scrolls when the available results exceed the visible area. The UI will show page numbers when there are multiple pages.
- If fewer than three actual predictions are returned, the plugin pads the display with `NO DATA` rows to maintain a consistent layout.

Time formats shown by the plugin:
- `ARR` — arriving now
- `BRD` — boarding now
- `X MIN` — X minutes until arrival
- `--` — unknown / no data

Line colors are taken from `LINE_CODES` in [manager.py](manager.py), and the plugin uses those colors to render text for each train.

## WMATA API

Endpoint used:
`https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{StationCode}`

Requests include the `api_key` header. See WMATA developer docs for rate limits and API details: https://developer.wmata.com/

## Troubleshooting

- "NO DATA" shown: verify `wmata_api_key` is correct and the `reference_station` is spelled as expected.
- API errors / rate limiting: increase `refresh_interval` or review the WMATA account limits.
- Logs: check your LEDMatrix/plugin logs for detailed errors.

## Files of interest
- Configuration schema: [config_schema.json](config_schema.json)
- Plugin implementation: [manager.py](manager.py)

## License

MIT

## Support

Open an issue in the github repository.
