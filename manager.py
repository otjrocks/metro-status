"""
DC Metro Status Plugin for LEDMatrix

Displays real-time Washington DC Metro train arrivals by direction,
similar to displays at actual metro stations.

API Version: 1.0.0
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any
import requests
from src.plugin_system.base_plugin import BasePlugin

# Station codes for DC Metro (common stations)
STATION_CODES = {
    "metro center": "A001",
    "gallery place": "A002",
    "archives": "A003",
    "judiciary square": "A004",
    "union station": "A005",
    "noma-gallaudet u": "A006",
    "rhode island ave": "A007",
    "brookland-cua": "A008",
    "fort totten": "A009",
    "takoma": "A010",
    "silver spring": "A011",
    "forest glen": "A012",
    "wheaton": "A013",
    "glenmont": "A014",
    "farragut north": "B01",
    "dupont circle": "B02",
    "woodley park": "B03",
    "cleveland park": "B04",
    "van ness-udc": "B05",
    "tenleytown": "B06",
    "friendship heights": "B07",
    "bethesda": "B08",
    "medical center": "B09",
    "glenmont": "B10",
    "farragut west": "C02",
    "foggy bottom": "C03",
    "george washington u": "C04",
    "circle line": "C05",
    "judiciary square": "C06",
    "metro center": "C01",
    "gallery place": "C07",
    "archives": "C08",
    "l'enfant plaza": "D01",
    "waterfront": "D02",
    "navy yard": "D03",
    "anacostia": "D04",
    "congress heights": "D05",
    "southern avenue": "D06",
    "naylor road": "D07",
    "suitland": "D08",
    "branch ave": "D09",
    "l'enfant plaza": "E01",
    "smith ave": "E02",
    "capitol south": "E03",
    "eastern market": "E04",
    "potomac ave": "E05",
    "stadium-armory": "E06",
    "minnesota ave": "E07",
    "deanwood": "E08",
    "ikea": "E09",
    "naylor road": "E10",
    "courthouse": "K01",
    "clarendon": "K02",
    "virginia square": "K03",
    "ballston": "K04",
    "west falls church": "K05",
    "east falls church": "K06",
    "falls church": "K07",
    "vienna": "K08",
    "dunn loring": "K09",
    "west falls church": "K10",
    "ashburn": "N06",
    "wfc metro": "K08",
    "largo town center": "F10",
}

# Line codes
LINE_CODES = {
    "RD": {"name": "Red", "color": (255, 0, 0)},
    "BL": {"name": "Blue", "color": (0, 0, 255)},
    "SV": {"name": "Silver", "color": (145, 145, 145)},
    "OR": {"name": "Orange", "color": (255, 165, 0)},
    "GR": {"name": "Green", "color": (0, 128, 0)},
    "YL": {"name": "Yellow", "color": (255, 255, 0)},
}

class BasePlugin:
    """Base class for all plugins - placeholder for local testing"""
    def __init__(self, plugin_id: str, config: Dict[str, Any], 
                 display_manager=None, cache_manager=None, plugin_manager=None):
        self.plugin_id = plugin_id
        self.config = config
        self.display_manager = display_manager
        self.cache_manager = cache_manager
        self.plugin_manager = plugin_manager
        self.logger = logging.getLogger(self.__class__.__name__)

class MetroStatusPlugin(BasePlugin):
    """
    WMATA Metro Status Plugin for displaying real-time train arrivals.
    
    Displays next 3 trains in each direction for a configured reference station.
    Train line names display in their official colors (Red, Blue, Orange, Silver, etc.).
    
    Configuration options:
        enabled (bool): Enable or disable the plugin (default: True)
        wmata_api_key (str): Your WMATA API key from https://developer.wmata.com/
        reference_station (str): The metro station to display arrivals for
        refresh_interval (int): How often to refresh train data in seconds (default: 30)
        page_display_time (int): How long to display each direction in seconds (default: 10)
        display_options (dict): Fine-grained control over text display behavior
            - show_line_abbreviation: Show train line abbreviation (default: True)
            - scroll_long_destinations: Scroll long destination names (default: True)
            - scroll_speed: Text scroll speed divisor (default: 5)
    """

    def __init__(self, plugin_id: str, config: Dict[str, Any],
                 display_manager=None, cache_manager=None, plugin_manager=None):
        """Initialize the metro status plugin."""
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)
        
        # Metro Status specific configuration
        self.enabled = config.get("enabled", True)
        self.wmata_api_key = config.get("wmata_api_key", "")
        self.reference_station = config.get("reference_station", "Metro Center").lower()
        self.station_code = self._get_station_code(self.reference_station)
        self.refresh_interval = config.get("refresh_interval", 30)
        self.page_display_time = config.get("page_display_time", 10)
        
        # Display options
        display_opts = config.get("display_options", {})
        self.show_line_abbreviation = display_opts.get("show_line_abbreviation", True)
        self.scroll_long_destinations = display_opts.get("scroll_long_destinations", True)
        self.scroll_speed = display_opts.get("scroll_speed", 5)
        
        # Current state - single page with next trains
        self.train_data = []  # List of next trains in order
        self.actual_train_count = 0  # Number of actual trains (not NO DATA padding)
        self.last_update = None
        
        # Scrolling state
        self.scroll_offset = 0  # Vertical scroll offset in pixels
        self.last_rendered_data = None  # Track last rendered data to detect changes
        self.last_scroll_offset = None  # Track last scroll offset to detect scroll changes
        
        # WMATA API endpoint
        self.predictions_api_url = "https://api.wmata.com/StationPrediction.svc/json/GetPrediction"
        
        self.logger.info(f"Metro Status plugin initialized for station: {self.reference_station}")
        self.logger.info(f"Configuration: refresh={self.refresh_interval}s, page_time={self.page_display_time}s")
        
        # Perform initial data fetch
        try:
            self._fetch_arrivals()
            self.logger.info("Initial train data fetch completed")
        except Exception as e:
            self.logger.warning(f"Initial fetch failed (will retry): {e}")
    
    def _get_station_code(self, station_name: str) -> str:
        """Get WMATA station code from station name"""
        return STATION_CODES.get(station_name.lower(), "A001")
    
    def _get_line_color(self, line_code: str) -> tuple:
        """Get RGB color for line"""
        return LINE_CODES.get(line_code, {}).get("color", (255, 255, 255))
    
    def _fetch_arrivals(self) -> bool:
        """Fetch real-time train arrival data from WMATA API"""
        try:
            if not self.wmata_api_key:
                self.logger.warning("No WMATA API key configured")
                return False
            
            # WMATA API endpoint for station predictions
            url = f"{self.predictions_api_url}/{self.station_code}"
            headers = {
                "api_key": self.wmata_api_key,
                "Cache-Control": "no-cache"
            }
            
            self.logger.debug(f"Fetching arrivals from {url}")
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Log raw response for debugging
            self.logger.debug(f"API response: {data}")
            
            # Parse arrival data and separate by direction
            self._parse_arrivals(data)
            self.last_update = datetime.now()
            self.logger.info(f"Successfully fetched train data for {self.reference_station}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch arrivals: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error fetching arrivals: {e}", exc_info=True)
            return False
    
    def _parse_arrivals(self, data: Dict[str, Any]) -> None:
        """Parse arrival data and store next trains"""
        try:
            # Initialize train list
            self.train_data = []
            
            trains = data.get("Trains", [])
            self.logger.debug(f"Processing {len(trains)} trains from API")
            
            # Process trains in order - get all of them for scrolling
            for train in trains:
                # Get train information
                destination_name = train.get("DestinationName", "").strip()
                line = train.get("Line", "")
                minutes = train.get("Min", "")
                
                # Format minutes for display
                if minutes == "ARR":
                    minutes_display = "ARR"
                elif minutes == "BRD":
                    minutes_display = "BRD"
                else:
                    try:
                        minutes_display = f"{int(minutes)} MIN"
                    except (ValueError, TypeError):
                        minutes_display = "--"
                
                train_info = {
                    "destination": destination_name,
                    "line": line,
                    "minutes": minutes_display,
                    "color": self._get_line_color(line)
                }
                
                self.train_data.append(train_info)
                self.logger.debug(f"Added train: {destination_name} - {minutes_display} ({line})")
            
            # Track how many actual trains we have
            self.actual_train_count = len(self.train_data)
            
            # Fill remaining slots with "NO DATA" if less than 3 trains (for minimum display)
            while len(self.train_data) < 3:
                self.train_data.append({
                    "destination": "NO DATA",
                    "line": "",
                    "minutes": "--",
                    "color": (255, 255, 255)
                })
            
            self.logger.info(f"Parsed {len(trains)} trains for {self.reference_station}, showing {self.actual_train_count} actual trains")
                    
        except Exception as e:
            self.logger.error(f"Error parsing arrivals: {e}", exc_info=True)
            self.train_data = [
                {"destination": "ERROR", "line": "", "minutes": "--", "color": (255, 255, 255)},
                {"destination": "ERROR", "line": "", "minutes": "--", "color": (255, 255, 255)},
                {"destination": "ERROR", "line": "", "minutes": "--", "color": (255, 255, 255)}
            ]
            self.actual_train_count = 0
    
    def _get_direction(self, destination: str) -> str:
        """Determine direction based on destination"""
        destination_lower = destination.lower()
        
        # East direction destinations (towards Largo/Branch Ave/Largo Town Center)
        east_destinations = ["largo", "branch", "suitland", "naylor", "congress", "southern", "navy yard", "anacostia", "waterfront", "ikea"]
        
        # West direction destinations (towards Vienna/Ashburn/Shady Grove/Glenmont)
        west_destinations = ["vienna", "ashburn", "dunn loring", "falls church", "west falls", "friendship heights", "bethesda", "medical center", "shady grove", "glenmont", "uptown", "tenleytown", "van ness"]
        
        for dest in east_destinations:
            if dest in destination_lower:
                return "east"
        
        for dest in west_destinations:
            if dest in destination_lower:
                return "west"
        
        # Default to east if destination is unclear
        return "east"
    
    
    def update(self) -> None:
        """Update train arrival data from WMATA API."""
        try:
            if not self.enabled:
                self.logger.debug("Metro Status plugin is disabled")
                return
            
            self._fetch_arrivals()
        except Exception as e:
            self.logger.error(f"Error updating metro status: {e}", exc_info=True)
    
    def display(self, force_clear: bool = False) -> Dict[str, Any]:
        """Display next 6 trains for the reference station with vertical scrolling.
        
        Args:
            force_clear: If True, clear display before rendering
            
        Returns:
            Dictionary containing display data
        """
        try:
            if not self.enabled or not self.display_manager:
                return {"station": self.reference_station, "trains": []}
            
            # Get display dimensions for proper positioning
            display_width = self.display_manager.width
            display_height = self.display_manager.height
            
            # Station header dimensions
            header_height = 7
            
            # Display trains with larger line height
            line_height = 8
            
            # Calculate how many trains can actually fit on screen
            available_height = display_height - header_height - 2
            max_visible_trains = max(3, available_height // line_height)  # At least 3, or however many fit
            
            # Check if data or scrolling has changed
            current_data_hash = hash(tuple((t["destination"], t["minutes"]) for t in self.train_data[:max_visible_trains]))
            data_changed = self.last_rendered_data != current_data_hash
            
            # Update scroll offset for smooth vertical scrolling
            # Only scroll if we have more actual trains than can fit on screen
            if self.actual_train_count > max_visible_trains:
                # Calculate total scroll range
                total_train_height = self.actual_train_count * line_height
                visible_height = display_height - header_height - 2
                max_scroll = max(0, total_train_height - visible_height)
                
                # Scroll faster: increment by 7 pixels per call for faster animation
                if not hasattr(self, '_scroll_step'):
                    self._scroll_step = 0
                
                self._scroll_step += 7 # Adjust this value for faster/slower scrolling
                
                # Create a loop that scrolls through all trains
                cycle_period = max_scroll + line_height
                if cycle_period > 0:
                    self.scroll_offset = int(self._scroll_step % cycle_period)
                else:
                    self.scroll_offset = 0
            else:
                self.scroll_offset = 0
            
            # Only update display if scroll offset changed or data changed
            scroll_changed = self.last_scroll_offset != self.scroll_offset
            
            if not data_changed and not scroll_changed and not force_clear:
                return {"station": self.reference_station, "trains": []}
            
            # Clear display for new content
            self.display_manager.clear()
            
            # Display station header with scrolling
            station_name = self.reference_station.title()
            station_font = self.display_manager.small_font
            
            # Calculate available width for station name
            max_station_width = display_width - 10
            available_for_name = max_station_width
            
            # Truncate station name with ellipsis if needed
            truncated_name = station_name
            while self.display_manager.get_text_width(truncated_name, station_font) > available_for_name and len(truncated_name) > 1:
                truncated_name = truncated_name[:-1]
            
            if len(truncated_name) < len(station_name):
                truncated_name = truncated_name[:-2] + ".." if len(truncated_name) > 2 else ".."
            
            station_display = truncated_name
            
            # Draw station header at scrolling position
            station_y = 0 - self.scroll_offset
            self.display_manager.draw_text(
                station_display,
                x=0,
                y=station_y,
                color=(255, 255, 255),
                small_font=True
            )
            
            # If no trains, show "No Data" message
            if not self.train_data or all(t["destination"] == "NO DATA" for t in self.train_data):
                self.display_manager.draw_text(
                    "NO DATA",
                    x=5,
                    y=header_height - self.scroll_offset,
                    color=(255, 128, 0),
                    small_font=True
                )
                self.display_manager.update_display()
                self.last_rendered_data = current_data_hash
                self.last_scroll_offset = self.scroll_offset
                return {"station": self.reference_station, "trains": []}
            
            # Use smaller font for train display
            train_font = self.display_manager.small_font
            
            # Display trains with times on right, with vertical scrolling
            # Start trains below the header (which now scrolls with them)
            y_offset = header_height + 1
            
            # Show all actual trains for scrolling
            for i, train in enumerate(self.train_data):
                y_pos = y_offset + (i * line_height) - self.scroll_offset
                
                # Only draw if visible on screen
                if y_pos + line_height < 0 or y_pos > display_height:
                    continue
                
                destination = train["destination"]
                minutes_str = str(train["minutes"])
                color = train["color"]
                
                # Calculate width of minutes text
                minutes_width = self.display_manager.get_text_width(minutes_str, train_font)
                
                # Position minutes text on the right (with small margin)
                right_margin = 2
                minutes_x = display_width - minutes_width - right_margin
                
                # Calculate max width available for destination to avoid overlap
                spacing = 2
                max_dest_available = minutes_x - spacing
                
                # Truncate destination if it would overlap with minutes
                truncated_dest = destination
                while self.display_manager.get_text_width(truncated_dest, train_font) > max_dest_available and len(truncated_dest) > 1:
                    truncated_dest = truncated_dest[:-1]
                
                if len(truncated_dest) < len(destination):
                    truncated_dest = truncated_dest[:-2] + ".." if len(truncated_dest) > 2 else ".."
                
                # Draw destination on the left
                self.display_manager.draw_text(
                    truncated_dest,
                    x=0,
                    y=y_pos,
                    color=color,
                    small_font=True
                )
                
                # Draw minutes on the right
                self.display_manager.draw_text(
                    minutes_str,
                    x=minutes_x,
                    y=y_pos,
                    color=color,
                    small_font=True
                )
            
            # Update the physical display
            self.display_manager.update_display()
            
            # Track render state to avoid unnecessary updates
            self.last_rendered_data = current_data_hash
            self.last_scroll_offset = self.scroll_offset
            
            # Return data for logging/debugging
            display_data = {
                "station": self.reference_station,
                "trains": []
            }
            
            for train in self.train_data[:self.actual_train_count]:
                display_data["trains"].append({
                    "destination": train["destination"],
                    "minutes": train["minutes"],
                    "line": train["line"]
                })
            
            self.logger.debug(f"Displayed {len(display_data['trains'])} trains for {self.reference_station}")
            return display_data
            
        except Exception as e:
            self.logger.error(f"Error displaying metro status: {e}", exc_info=True)
            try:
                if self.display_manager:
                    self.display_manager.clear()
                    self.display_manager.draw_text(
                        "ERROR",
                        x=5,
                        y=15,
                        color=(255, 0, 0),
                        small_font=True
                    )
                    self.display_manager.update_display()
            except:
                pass
            return {"station": self.reference_station, "trains": []}
            
        except Exception as e:
            self.logger.error(f"Error displaying metro status: {e}", exc_info=True)
            try:
                if self.display_manager:
                    self.display_manager.clear()
                    self.display_manager.draw_text(
                        "ERROR",
                        x=5,
                        y=15,
                        color=(255, 0, 0),
                        small_font=True
                    )
                    self.display_manager.update_display()
            except:
                pass
            return {"direction": "ERROR", "trains": []}
    
    def next_page(self) -> None:
        """Next page - no-op since there's only one page."""
        pass
    
    def prev_page(self) -> None:
        """Previous page - no-op since there's only one page."""
        pass
    
    def get_display_duration(self) -> float:
        """Get display duration from config."""
        return float(self.page_display_time)
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        # Validate required fields
        if not self.wmata_api_key:
            self.logger.error("WMATA API key is required")
            return False
        
        if not self.reference_station:
            self.logger.error("Reference station is required")
            return False
        
        # Validate numeric ranges
        if not (10 <= self.refresh_interval <= 300):
            self.logger.error("Refresh interval must be between 10 and 300 seconds")
            return False
        
        if not (5 <= self.page_display_time <= 60):
            self.logger.error("Page display time must be between 5 and 60 seconds")
            return False
        
        if not (1 <= self.scroll_speed <= 20):
            self.logger.error("Scroll speed must be between 1 and 20")
            return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Return plugin info for web UI."""
        info = {
            "plugin_id": self.plugin_id,
            "enabled": self.enabled,
            "reference_station": self.reference_station,
            "trains_count": len(self.train_data),
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
        return info
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "reference_station": self.reference_station,
            "wmata_api_key": "***" if self.wmata_api_key else "Not configured",
            "refresh_interval": self.refresh_interval,
            "page_display_time": self.page_display_time
        }
