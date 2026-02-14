import json
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests
from abc import ABC

# Configure logging
logger = logging.getLogger(__name__)

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
    "SV": {"name": "Silver", "color": (192, 192, 192)},
    "OR": {"name": "Orange", "color": (255, 165, 0)},
    "GR": {"name": "Green", "color": (0, 128, 0)},
    "YL": {"name": "Yellow", "color": (255, 255, 0)},
}

class BasePlugin(ABC):
    """Base class for all plugins"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def update(self) -> None:
        """Update plugin data"""
        pass
    
    def display(self) -> None:
        """Display plugin data"""
        pass

class MetroStatusPlugin(BasePlugin):
    """WMATA Metro Status Plugin for displaying real-time train arrivals"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.wmata_api_key = self.config.get("wmata_api_key", "")
        self.reference_station = self.config.get("reference_station", "Metro Center").lower()
        self.station_code = self._get_station_code(self.reference_station)
        self.current_page = 0  # 0 for east, 1 for west
        self.train_data = {
            "east": [],
            "west": []
        }
        self.last_update = None
        # Correct WMATA API endpoint
        self.predictions_api_url = "https://api.wmata.com/StationPrediction.svc/json/GetPrediction"
    
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
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Parse arrival data and separate by direction
            self._parse_arrivals(data)
            self.last_update = datetime.now()
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch arrivals: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response: {e}")
            return False
    
    def _parse_arrivals(self, data: Dict[str, Any]) -> None:
        """Parse arrival data and organize by direction"""
        try:
            # Initialize train lists
            self.train_data = {"east": [], "west": []}
            
            trains = data.get("Trains", [])
            
            for train in trains:
                # Get destination name and line
                destination_name = train.get("DestinationName", "").strip()
                line = train.get("Line", "")
                minutes = train.get("Min", "")
                group = train.get("Group", "")
                
                # Determine direction based on Group field and destination
                direction = self._get_direction_from_group(destination_name, group)
                
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
                
                # Add to appropriate direction (limit to 3 trains per direction)
                if direction == "east" and len(self.train_data["east"]) < 3:
                    self.train_data["east"].append(train_info)
                elif direction == "west" and len(self.train_data["west"]) < 3:
                    self.train_data["west"].append(train_info)
            
            # Fill empty slots with placeholder data
            for direction in ["east", "west"]:
                while len(self.train_data[direction]) < 3:
                    self.train_data[direction].append({
                        "destination": "NO DATA",
                        "line": "",
                        "minutes": "--",
                        "color": (255, 255, 255)
                    })
                    
        except Exception as e:
            self.logger.error(f"Error parsing arrivals: {e}")
            self.train_data = {
                "east": [{"destination": "ERROR", "line": "", "minutes": "--", "color": (255, 255, 255)}] * 3,
                "west": [{"destination": "ERROR", "line": "", "minutes": "--", "color": (255, 255, 255)}] * 3
            }
    
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
    
    def _get_direction_from_group(self, destination: str, group: str) -> str:
        """Determine direction based on Group field and destination"""
        destination_lower = destination.lower()
        
        # East direction destinations (towards Largo/Branch Ave/Navy Yard/Anacostia)
        east_destinations = ["largo", "branch", "suitland", "naylor", "congress", "southern", "navy yard", "anacostia", "waterfront", "ikea", "deanwood", "minnesota"]
        
        # West direction destinations (towards Vienna/Ashburn/Shady Grove/Glenmont)
        west_destinations = ["vienna", "ashburn", "dunn loring", "falls church", "west falls", "friendship heights", "bethesda", "medical center", "shady grove", "shady grv", "glenmont", "uptown", "tenleytown", "van ness", "wheaton", "takoma", "silver spring", "noma"]
        
        for dest in east_destinations:
            if dest in destination_lower:
                return "east"
        
        for dest in west_destinations:
            if dest in destination_lower:
                return "west"
        
        # Use Group field as fallback (Group "1" vs "2" may indicate direction)
        if group == "1":
            return "east"
        elif group == "2":
            return "west"
        
        # Default to east if destination is unclear
        return "east"
    
    def update(self) -> None:
        """Update train arrival data"""
        self._fetch_arrivals()
    
    def display(self) -> Dict[str, Any]:
        """Get display data for current page"""
        direction = "east" if self.current_page == 0 else "west"
        direction_label = "EASTBOUND" if self.current_page == 0 else "WESTBOUND"
        
        trains = self.train_data.get(direction, [])
        
        display_data = {
            "direction": direction_label,
            "trains": []
        }
        
        for i, train in enumerate(trains[:3]):  # Ensure only 3 trains
            display_data["trains"].append({
                "destination": train["destination"][:17],  # Limit to 17 chars for display
                "minutes": train["minutes"],
                "color": train["color"],
                "line": train["line"]
            })
        
        return display_data
    
    def next_page(self) -> None:
        """Switch to next page (direction)"""
        self.current_page = (self.current_page + 1) % 2
    
    def prev_page(self) -> None:
        """Switch to previous page (direction)"""
        self.current_page = (self.current_page - 1) % 2
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "reference_station": self.reference_station,
            "wmata_api_key": "***" if self.wmata_api_key else "Not configured"
        }
