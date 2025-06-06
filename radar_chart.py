import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple
import matplotlib.patches as patches


class RadarChartPlotter:
    """Creates radar charts for basketball shooting statistics."""
    
    def __init__(self):
        # Standard shot zones in order for radar chart
        self.standard_zones = [
            'Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3',
            'Above Break 3', 'Left Mid Range', 'Free Throw Line', 'Right Mid Range', 'Paint'
        ]
        
        # Colors for different players
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    def prepare_data_for_radar(self, zone_percentages: Dict[str, float]) -> Tuple[List[str], List[float]]:
        """Prepare data in the correct order for radar chart."""
        labels = []
        values = []
        
        for zone in self.standard_zones:
            labels.append(zone.replace(' ', '\n'))  # Break long labels
            values.append(zone_percentages.get(zone, 0.0))
        
        return labels, values
    
    def create_radar_subplot(self, fig, position, title: str = "") -> Tuple:
        """Create a radar chart subplot."""
        ax = fig.add_subplot(position, projection='polar')
        ax.set_title(title, size=16, fontweight='bold', pad=20)
        
        # Set up the angle for each zone
        num_zones = len(self.standard_zones)
        angles = np.linspace(0, 2 * np.pi, num_zones, endpoint=False).tolist()
        
        # Close the plot
        angles += angles[:1]
        
        return ax, angles
    
    def plot_single_player_radar(self, 
                                zone_data: Dict[str, float], 
                                player_name: str = "Player",
                                title: Optional[str] = None,
                                color: str = '#1f77b4',
                                save_path: Optional[str] = None,
                                use_made_shots: bool = False) -> plt.Figure:
        """Create a radar chart for a single player."""
        
        labels, values = self.prepare_data_for_radar(zone_data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Set up angles
        num_zones = len(values)
        angles = np.linspace(0, 2 * np.pi, num_zones, endpoint=False).tolist()
        values += values[:1]  # Close the plot
        angles += angles[:1]
        
        # Plot the radar chart
        ax.plot(angles, values, 'o-', linewidth=2, label=player_name, color=color)
        ax.fill(angles, values, alpha=0.25, color=color)
        
        # Customize the chart based on data type
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        if use_made_shots:
            # Set up for made shots (count data)
            max_value = max(values[:-1]) if values[:-1] else 10
            max_scale = max(10, int(max_value * 1.2))  # 20% buffer above max
            ax.set_ylim(0, max_scale)
            
            # Create appropriate tick marks
            step = max(1, max_scale // 5)
            ticks = list(range(0, max_scale + 1, step))
            ax.set_yticks(ticks)
            ax.set_yticklabels([str(tick) for tick in ticks], fontsize=8)
            
            # Add value labels on the chart
            for angle, value, label in zip(angles[:-1], values[:-1], labels):
                if value > 0:
                    ax.text(angle, value + max_scale * 0.05, f'{int(value)}', 
                           horizontalalignment='center', fontsize=8, fontweight='bold')
        else:
            # Set up for percentages
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
            
            # Add percentage labels on the chart
            for angle, value, label in zip(angles[:-1], values[:-1], labels):
                if value > 0:
                    ax.text(angle, value + 5, f'{value:.0f}%', 
                           horizontalalignment='center', fontsize=8, fontweight='bold')
        
        ax.grid(True)
        
        # Add title
        data_type = "Made Shots" if use_made_shots else "Shot Chart Analysis"
        plot_title = title or f"{player_name} - {data_type}"
        plt.title(plot_title, size=16, fontweight='bold', pad=30)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_comparison_radar(self, 
                             player_data: Dict[str, Dict[str, float]], 
                             title: str = "Player Comparison",
                             save_path: Optional[str] = None,
                             use_made_shots: bool = False) -> plt.Figure:
        """Create a radar chart comparing multiple players."""
        
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
        
        player_names = list(player_data.keys())
        all_values = []
        
        for i, (player_name, zone_data) in enumerate(player_data.items()):
            labels, values = self.prepare_data_for_radar(zone_data)
            all_values.extend(values)
            
            # Set up angles
            num_zones = len(values)
            angles = np.linspace(0, 2 * np.pi, num_zones, endpoint=False).tolist()
            values += values[:1]  # Close the plot
            angles += angles[:1]
            
            # Get color for this player
            color = self.colors[i % len(self.colors)]
            
            # Plot the radar chart
            ax.plot(angles, values, 'o-', linewidth=2, label=player_name, color=color)
            ax.fill(angles, values, alpha=0.15, color=color)
        
        # Customize the chart based on data type
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        if use_made_shots:
            # Set up for made shots (count data)
            max_value = max(all_values) if all_values else 10
            max_scale = max(10, int(max_value * 1.2))  # 20% buffer above max
            ax.set_ylim(0, max_scale)
            
            # Create appropriate tick marks
            step = max(1, max_scale // 5)
            ticks = list(range(0, max_scale + 1, step))
            ax.set_yticks(ticks)
            ax.set_yticklabels([str(tick) for tick in ticks], fontsize=8)
        else:
            # Set up for percentages
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
        
        ax.grid(True)
        
        # Add title
        data_type = "Made Shots Comparison" if use_made_shots else "Player Comparison"
        plot_title = title if "Comparison" in title else data_type
        plt.title(plot_title, size=16, fontweight='bold', pad=30)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_detailed_comparison(self, 
                                player_data: Dict[str, Dict[str, float]],
                                title: str = "Detailed Player Comparison",
                                use_made_shots: bool = False) -> plt.Figure:
        """Create a detailed comparison with both radar and bar charts."""
        
        fig = plt.figure(figsize=(16, 8))
        
        # Radar chart on the left
        ax1 = fig.add_subplot(121, projection='polar')
        
        player_names = list(player_data.keys())
        all_values = []
        
        for i, (player_name, zone_data) in enumerate(player_data.items()):
            labels, values = self.prepare_data_for_radar(zone_data)
            all_values.extend(values)
            
            # Set up angles
            num_zones = len(values)
            angles = np.linspace(0, 2 * np.pi, num_zones, endpoint=False).tolist()
            values += values[:1]  # Close the plot
            angles += angles[:1]
            
            # Get color for this player
            color = self.colors[i % len(self.colors)]
            
            # Plot the radar chart
            ax1.plot(angles, values, 'o-', linewidth=2, label=player_name, color=color)
            ax1.fill(angles, values, alpha=0.15, color=color)
        
        # Customize radar chart based on data type
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels(labels, fontsize=9)
        
        if use_made_shots:
            # Set up for made shots (count data)
            max_value = max(all_values) if all_values else 10
            max_scale = max(10, int(max_value * 1.2))  # 20% buffer above max
            ax1.set_ylim(0, max_scale)
            
            # Create appropriate tick marks
            step = max(1, max_scale // 5)
            ticks = list(range(0, max_scale + 1, step))
            ax1.set_yticks(ticks)
            ax1.set_yticklabels([str(tick) for tick in ticks], fontsize=8)
        else:
            # Set up for percentages
            ax1.set_ylim(0, 100)
            ax1.set_yticks([20, 40, 60, 80, 100])
            ax1.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
        
        ax1.grid(True)
        ax1.set_title("Radar Comparison", fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        
        # Bar chart on the right
        ax2 = fig.add_subplot(122)
        
        zones = self.standard_zones
        x_pos = np.arange(len(zones))
        width = 0.35
        
        for i, (player_name, zone_data) in enumerate(player_data.items()):
            values = [zone_data.get(zone, 0.0) for zone in zones]
            color = self.colors[i % len(self.colors)]
            
            offset = (i - len(player_names)/2 + 0.5) * width
            ax2.bar(x_pos + offset, values, width, label=player_name, color=color, alpha=0.8)
        
        ax2.set_xlabel('Shot Zones', fontweight='bold')
        
        if use_made_shots:
            ax2.set_ylabel('Made Shots Count', fontweight='bold')
            ax2.set_title('Bar Chart Comparison (Made Shots)', fontsize=14, fontweight='bold')
            max_bar_value = max([max(zone_data.values()) for zone_data in player_data.values()]) if player_data else 10
            ax2.set_ylim(0, max_bar_value * 1.1)
        else:
            ax2.set_ylabel('Shooting Percentage (%)', fontweight='bold')
            ax2.set_title('Bar Chart Comparison', fontsize=14, fontweight='bold')
            ax2.set_ylim(0, 100)
        
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([zone.replace(' ', '\n') for zone in zones], rotation=45, ha='right')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        data_type = "Made Shots" if use_made_shots else "Shooting Percentages"
        plt.suptitle(f"{title} - {data_type}", fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        return fig


if __name__ == "__main__":
    # Test the radar chart plotter
    plotter = RadarChartPlotter()
    
    # Sample data
    sample_data = {
        'Left Corner 3': 45.0,
        'Left Wing 3': 38.0,
        'Top of Key 3': 35.0,
        'Right Wing 3': 42.0,
        'Right Corner 3': 48.0,
        'Above Break 3': 33.0,
        'Left Mid Range': 52.0,
        'Free Throw Line': 65.0,
        'Right Mid Range': 48.0,
        'Paint': 72.0
    }
    
    # Test single player radar
    fig1 = plotter.plot_single_player_radar(sample_data, "Test Player")
    plt.show()
    
    # Test comparison radar
    comparison_data = {
        "Player A": sample_data,
        "Player B": {zone: val + np.random.uniform(-10, 10) for zone, val in sample_data.items()}
    }
    
    fig2 = plotter.plot_comparison_radar(comparison_data)
    plt.show() 