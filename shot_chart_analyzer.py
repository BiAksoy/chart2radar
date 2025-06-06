from typing import List, Dict, Tuple
from ocr_extractor import ShotChartOCR
import json

class ShotChartAnalyzer:
    """Complete shot chart analyzer with OCR detection and proper zone mapping."""
    
    def __init__(self):
        # Basketball court zones based on actual position analysis
        self.zones = {
            'Left Corner 3': {
                'x_range': (50, 120),
                'y_range': (20, 80),
                'description': 'Bottom left corner three-point area'
            },
            'Right Corner 3': {
                'x_range': (650, 720),
                'y_range': (20, 80),
                'description': 'Bottom right corner three-point area'
            },
            'Left Mid Range': {
                'x_range': (170, 210),
                'y_range': (100, 160),
                'description': 'Left side mid-range area'
            },
            'Paint': {
                'x_range': (300, 440),
                'y_range': (20, 40),
                'description': 'Paint/key area'
            },
            'Free Throw Line': {  # Combined free throw line zone
                'x_range': (270, 480),
                'y_range': (240, 270),
                'description': 'Free throw line area'
            },
            'Left Wing 3': {
                'x_range': (80, 130),
                'y_range': (350, 420),
                'description': 'Left wing three-point area'
            },
            'Right Wing 3': {
                'x_range': (610, 660),
                'y_range': (350, 420),
                'description': 'Right wing three-point area'
            },
            'Top of Key 3': {
                'x_range': (350, 400),
                'y_range': (480, 550),
                'description': 'Top of the key three-point area'
            },

            'Right Mid Range': {  # For stats around (557, 109) and (557, 147)
                'x_range': (540, 580),
                'y_range': (100, 160),
                'description': 'Right side mid-range area'
            }
        }
    
    def map_stat_to_zone(self, stat: Dict) -> str:
        """Map a detected statistic to its basketball court zone."""
        x, y = stat['center_x'], stat['center_y']
        
        for zone_name, zone_def in self.zones.items():
            if (zone_def['x_range'][0] <= x <= zone_def['x_range'][1] and
                zone_def['y_range'][0] <= y <= zone_def['y_range'][1]):
                return zone_name
        
        return 'Unknown Zone'
    
    def analyze_shot_chart(self, image_path: str) -> Dict:
        """Analyze a shot chart and return properly mapped basketball statistics."""
        # Get OCR results
        ocr = ShotChartOCR()
        raw_stats = ocr.extract_basketball_stats(image_path)
        
        # Filter out inferred N/A values for zone mapping
        actual_stats = [s for s in raw_stats if s.get('method') != 'inferred_na']
        
        # Initialize zones
        zone_data = {}
        for zone_name in self.zones.keys():
            zone_data[zone_name] = {
                'shots_made_attempted': 'N/A',
                'percentage': '0.0%',
                'detected_stats': []
            }
        
        # Map each stat to its zone
        for stat in actual_stats:
            zone = self.map_stat_to_zone(stat)
            if zone != 'Unknown Zone':
                zone_data[zone]['detected_stats'].append(stat)
        
        # Process each zone to extract shots and percentages
        for zone_name, data in zone_data.items():
            stats = data['detected_stats']
            if stats:
                # Find shots (contains '/') and percentages (contains '%')
                shots = [s for s in stats if '/' in s['text']]
                percentages = [s for s in stats if '%' in s['text']]
                
                if zone_name == 'Free Throw Line' and len(shots) == 2:
                    # Special handling for Free Throw Line - combine left and right
                    # Find left side (lower x) and right side (higher x)
                    left_shot = min(shots, key=lambda s: s['center_x'])
                    right_shot = max(shots, key=lambda s: s['center_x'])
                    data['shots_made_attempted'] = f"{left_shot['text']} + {right_shot['text']}"
                elif shots:
                    data['shots_made_attempted'] = shots[0]['text']
                    
                if percentages:
                    data['percentage'] = percentages[0]['text']
        
        # Create final report
        player_name = image_path.split('/')[-1].replace('.jpeg', '').replace('_', ' ').title()
        
        # Create ordered output matching the desired format
        ordered_zones = [
            'Left Corner 3',
            'Left Wing 3', 
            'Top of Key 3',
            'Right Wing 3',
            'Right Corner 3',
            'Left Mid Range',
            'Left Free Throw',
            'Right Free Throw',
            'Right Mid Range',
            'Paint'
        ]
        
        final_report = []
        for i, zone_name in enumerate(ordered_zones):
            zone_info = zone_data.get(zone_name, {})
            final_report.append({
                'index': i,
                'zone': zone_name,
                'shots_made_attempted': zone_info.get('shots_made_attempted', 'N/A'),
                'percentage': zone_info.get('percentage', '0.0%')
            })
        
        return {
            'player': player_name,
            'statistics': final_report,
            'total_detected': len(actual_stats),
            'raw_detections': actual_stats
        }
    
    def print_report(self, image_path: str):
        """Print a formatted report for the shot chart."""
        report = self.analyze_shot_chart(image_path)
        
        print(f"SHOT CHART ANALYSIS: {report['player']}")
        print("="*60)
        print(f"Total statistics detected: {report['total_detected']}")
        print()
        
        for stat in report['statistics']:
            print(f"{stat['index']}\t{stat['zone']}\t{stat['shots_made_attempted']}\t{stat['percentage']}")
        
        print(f"\nDetailed positions:")
        for detection in report['raw_detections']:
            zone = self.map_stat_to_zone(detection)
            print(f"  '{detection['text']}' at ({detection['center_x']}, {detection['center_y']}) -> {zone}")

def test_analyzer():
    """Test the shot chart analyzer."""
    analyzer = ShotChartAnalyzer()
    
    print("TESTING SHOT CHART ANALYZER")
    print("="*80)
    
    # Test on Marina Mabrey
    analyzer.print_report("shot_charts/marina_mabrey.jpeg")

if __name__ == "__main__":
    test_analyzer() 