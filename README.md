# DC Metro Status Plugin

Display real-time Washington DC Metro train arrivals by direction on your LED Matrix, similar to station displays at actual metro stations.

## Features

- **Real-time Train Arrivals**: Fetches live train arrival data from the WMATA API
- **Directional Display**: Shows next 3 trains in both directions on separate pages:
  - First page: Eastbound trains (toward Largo/Branch Ave)
  - Second page: Westbound trains (toward Vienna/Ashburn/Shady Grove)
- **Line-colored Text**: Train line names display in their official colors:
  - Red (RD)
  - Blue (BL)
  - Silver (SV)
  - Orange (OR)
  - Green (GR)
  - Yellow (YL)
- **Configurable Station**: Set any DC Metro station as the reference point
- **Auto-refresh**: Configurable refresh interval to always show current data

## Installation

1. **Get a WMATA API Key**:
   - Visit https://developer.wmata.com/
   - Sign up for a free account
   - Get your API key from your account dashboard

2. **Install the Plugin**:
   - Via LEDMatrix Web UI: Plugin Store → Search "DC Metro" → Install
   - Or manually copy this directory to `LEDMatrix/plugin-repos/wmata-metro-status`

## Configuration

### config.json

Create a `config.json` file in the plugin directory with your settings:

```json
{
  "reference_station": "Courthouse",
  "wmata_api_key": "your_api_key_here",
  "refresh_interval": 30,
  "page_display_time": 10
}
```

### config-secret.json (Recommended)

For security, store your API key in `config-secret.json`:

```json
{
  "wmata_api_key": "your_api_key_here"
}
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `reference_station` | string | Yes | - | Metro station name (e.g., "Courthouse", "Metro Center", "Gallery Place") |
| `wmata_api_key` | string | Yes | - | Your WMATA Developer API key |
| `refresh_interval` | integer | No | 30 | Seconds between API calls (10-300) |
| `page_display_time` | integer | No | 10 | Seconds to display each direction (5-60) |

## Example Stations

The plugin supports all DC Metro stations. Common examples:

### Red Line
- Metro Center
- Gallery Place
- Union Station
- Silver Spring
- Glenmont

### Blue/Silver Line
- Farragut West
- L'Enfant Plaza
- Pentagon
- DCA Airport

### Orange/Silver Line
- Courthouse
- Ballston
- Vienna
- Ashburn

### Green Line
- Gallery Place
- L'Enfant Plaza
- Navy Yard
- Branch Avenue

### Yellow Line
- Gallery Place
- Metro Center
- Navy Yard

## Display Output

### First Page (Eastbound)
```
STATION_A           1 MIN
STATION_B           5 MIN
STATION_C          10 MIN
```
(Text color matches the train line color)

### Second Page (Westbound)
```
STATION_X           ARR
STATION_Y          10 MIN
STATION_Z          20 MIN
```

## Time Formats

- `ARR` - Train arriving now
- `BRD` - Boarding now
- `X MIN` - Minutes until arrival
- `--` - No data available

## Troubleshooting

### No Data Displays
- Verify your API key is correct
- Check that your reference station name is valid
- Ensure your WMATA API key has proper permissions
- Check the LEDMatrix logs: `journalctl -u ledmatrix -f`

### API Errors
- Rate limiting: Default refresh is 30 seconds, adjust if needed
- Invalid station: Verify the exact station name
- API key issues: Regenerate your key at https://developer.wmata.com/

### Common Station Names
Use exact station names as they appear on metro signs. The plugin performs fuzzy matching, so variations usually work:
- "Courthouse" (not "Court House")
- "Metro Center" (not "Metro Station")
- "Gallery Place" (not "Gallery Pl")

## API Reference

This plugin uses the WMATA StationPrediction API:
- Endpoint: `https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{StationCode}`
- Authentication: API key in request headers
- Rate Limit: Default 10 requests/second (free tier)

For more info: https://developer.wmata.com/api-details

## License

MIT License

## Support

- Issues: https://github.com/ChuckBuilds/ledmatrix-plugins/issues
- Discord: https://discord.gg/uW36dVAtcT
- WMATA API Support: api-support@wmata.com

## Author

Created as a community plugin for the LEDMatrix project by ChuckBuilds.
Authored by Owen Jennings using Claude Haiku 4.5
