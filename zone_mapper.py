import re
from typing import Dict, List, Tuple, Optional
import numpy as np


class ShotZoneMapper:
    """Maps OCR extracted text to basketball shot zones based on coordinates."""
    
    def __init__(self):
        # Define shot zones with their approximate bounding boxes
        # These coordinates are relative to a standard basketball shot chart
        # Adjust these based on your shot chart image dimensions
        self.shot_zones = {
            'Left Corner 3': {'x_range': (0, 150), 'y_range': (300, 500)},
            'Right Corner 3': {'x_range': (650, 800), 'y_range': (300, 500)},
            'Left Wing 3': {'x_range': (50, 250), 'y_range': (150, 300)},
            'Right Wing 3': {'x_range': (550, 750), 'y_range': (150, 300)},
            'Top of Key 3': {'x_range': (250, 550), 'y_range': (50, 200)},
            'Above Break 3': {'x_range': (200, 600), 'y_range': (100, 250)},
            'Left Mid Range': {'x_range': (150, 350), 'y_range': (200, 400)},
            'Right Mid Range': {'x_range': (450, 650), 'y_range': (200, 400)},
            'Paint': {'x_range': (300, 500), 'y_range': (350, 550)},
            'Free Throw Line': {'x_range': (250, 550), 'y_range': (250, 350)},
        }
        
        # Standard shot zones in order for radar chart
        self.standard_zones = [
            'Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3',
            'Above Break 3', 'Left Mid Range', 'Free Throw Line', 'Right Mid Range', 'Paint'
        ]
    
    def point_in_zone(self, x: int, y: int, zone_bounds: Dict) -> bool:
        """Check if a point (x, y) falls within a zone's boundaries."""
        x_min, x_max = zone_bounds['x_range']
        y_min, y_max = zone_bounds['y_range']
        
        return x_min <= x <= x_max and y_min <= y <= y_max
    
    def get_zone_for_coordinate(self, x: int, y: int) -> Optional[str]:
        """Get the shot zone for given coordinates."""
        for zone_name, zone_bounds in self.shot_zones.items():
            if self.point_in_zone(x, y, zone_bounds):
                return zone_name
        
        # If no exact match, find the closest zone
        return self.get_closest_zone(x, y)
    
    def get_closest_zone(self, x: int, y: int) -> str:
        """Find the closest zone to given coordinates."""
        min_distance = float('inf')
        closest_zone = 'Paint'  # Default fallback
        
        for zone_name, zone_bounds in self.shot_zones.items():
            # Calculate distance to zone center
            x_center = (zone_bounds['x_range'][0] + zone_bounds['x_range'][1]) / 2
            y_center = (zone_bounds['y_range'][0] + zone_bounds['y_range'][1]) / 2
            
            distance = np.sqrt((x - x_center)**2 + (y - y_center)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_zone = zone_name
        
        return closest_zone
    
    def is_made_attempts(self, text: str) -> bool:
        """Check if text is in made/attempts format (e.g., '27/70')."""
        return bool(re.match(r'^\d+/\d+$', text.strip()))
    
    def is_percentage(self, text: str) -> bool:
        """Check if text is a percentage (e.g., '38.6%')."""
        return bool(re.match(r'^\d+\.?\d*%$', text.strip()))
    
    def parse_made_attempts(self, text: str) -> Tuple[int, int]:
        """Parse made/attempts text into tuple of (made, attempts)."""
        if self.is_made_attempts(text):
            made, attempts = text.split('/')
            return int(made), int(attempts)
        return 0, 0
    
    def parse_percentage(self, text: str) -> float:
        """Parse percentage text into float value."""
        if self.is_percentage(text):
            return float(text.replace('%', ''))
        return 0.0
    
    def group_stats_by_proximity(self, ocr_results: List[Dict], proximity_threshold: int = 100) -> List[List[Dict]]:
        """Group OCR results that are close to each other (likely same zone stats)."""
        groups = []
        used_indices = set()
        
        for i, result in enumerate(ocr_results):
            if i in used_indices:
                continue
                
            group = [result]
            used_indices.add(i)
            
            for j, other_result in enumerate(ocr_results):
                if j in used_indices:
                    continue
                    
                # Calculate distance between centers
                distance = np.sqrt(
                    (result['center_x'] - other_result['center_x'])**2 + 
                    (result['center_y'] - other_result['center_y'])**2
                )
                
                if distance <= proximity_threshold:
                    group.append(other_result)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def extract_zone_stats(self, group: List[Dict]) -> Dict:
        """Extract statistics from a group of OCR results in the same zone."""
        zone_stat = {
            'made': 0,
            'attempts': 0,
            'percentage': 0.0,
            'zone': None,
            'coordinates': []
        }
        
        # Determine zone based on the first coordinate in the group
        if group:
            first_coord = group[0]
            zone_stat['zone'] = self.get_zone_for_coordinate(
                first_coord['center_x'], 
                first_coord['center_y']
            )
        
        for result in group:
            zone_stat['coordinates'].append((result['center_x'], result['center_y']))
            
            if self.is_made_attempts(result['text']):
                made, attempts = self.parse_made_attempts(result['text'])
                zone_stat['made'] = made
                zone_stat['attempts'] = attempts
                # Calculate percentage if not already provided
                if attempts > 0 and zone_stat['percentage'] == 0.0:
                    zone_stat['percentage'] = (made / attempts) * 100
                    
            elif self.is_percentage(result['text']):
                zone_stat['percentage'] = self.parse_percentage(result['text'])
        
        return zone_stat
    
    def map_ocr_to_zones(self, ocr_results: List[Dict]) -> Dict[str, Dict]:
        """Main method to map OCR results to shot zones with statistics."""
        # Group nearby OCR results
        groups = self.group_stats_by_proximity(ocr_results)
        
        zone_data = {}
        
        for group in groups:
            zone_stat = self.extract_zone_stats(group)
            zone_name = zone_stat['zone']
            
            if zone_name and (zone_stat['made'] > 0 or zone_stat['percentage'] > 0):
                # If zone already exists, combine the stats
                if zone_name in zone_data:
                    existing = zone_data[zone_name]
                    # Take the better/more complete stat
                    if zone_stat['attempts'] > existing.get('attempts', 0):
                        zone_data[zone_name] = zone_stat
                else:
                    zone_data[zone_name] = zone_stat
        
        return zone_data
    
    def get_normalized_zone_percentages(self, zone_data: Dict[str, Dict]) -> Dict[str, float]:
        """Convert zone data to normalized percentages for radar chart."""
        normalized_data = {}
        
        for zone in self.standard_zones:
            if zone in zone_data:
                percentage = zone_data[zone].get('percentage', 0.0)
                normalized_data[zone] = percentage
            else:
                normalized_data[zone] = 0.0
        
        return normalized_data

    def get_normalized_zone_made_shots(self, zone_data: Dict[str, Dict]) -> Dict[str, int]:
        """Convert zone data to normalized made shot counts for radar chart."""
        normalized_data = {}
        
        for zone in self.standard_zones:
            if zone in zone_data:
                made_shots = zone_data[zone].get('made', 0)
                normalized_data[zone] = made_shots
            else:
                normalized_data[zone] = 0
        
        return normalized_data

    def get_normalized_zone_attempts(self, zone_data: Dict[str, Dict]) -> Dict[str, int]:
        """Convert zone data to normalized attempt counts for radar chart."""
        normalized_data = {}
        
        for zone in self.standard_zones:
            if zone in zone_data:
                attempts = zone_data[zone].get('attempts', 0)
                normalized_data[zone] = attempts
            else:
                normalized_data[zone] = 0
        
        return normalized_data


if __name__ == "__main__":
    # Test the zone mapper
    from ocr_extractor import ShotChartOCR
    
    # Extract OCR data
    ocr = ShotChartOCR()
    ocr_results = ocr.extract_basketball_stats("shot_charts/marina_mabrey.jpeg")
    
    # Map to zones
    mapper = ShotZoneMapper()
    zone_data = mapper.map_ocr_to_zones(ocr_results)
    
    print("Zone Statistics:")
    for zone, stats in zone_data.items():
        print(f"{zone}: {stats['made']}/{stats['attempts']} ({stats['percentage']:.1f}%)")
    
    print("\nNormalized for Radar Chart:")
    normalized = mapper.get_normalized_zone_percentages(zone_data)
    for zone, percentage in normalized.items():
        print(f"{zone}: {percentage:.1f}%") 