import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import json
import os


class PlayerSimilarityFinder:
    """Finds the most similar players based on shooting zone statistics."""
    
    def __init__(self):
        # Standard shot zones for consistent comparison
        self.standard_zones = [
            'Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3',
            'Above Break 3', 'Left Mid Range', 'Free Throw Line', 'Right Mid Range', 'Paint'
        ]
    
    def normalize_player_data(self, player_data: Dict[str, Dict[str, float]]) -> Dict[str, List[float]]:
        """Normalize player data to consistent format for comparison."""
        normalized_data = {}
        
        for player_name, zone_percentages in player_data.items():
            # Create vector with all standard zones
            player_vector = []
            for zone in self.standard_zones:
                percentage = zone_percentages.get(zone, 0.0)
                player_vector.append(percentage)
            
            normalized_data[player_name] = player_vector
        
        return normalized_data
    
    def compute_cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Compute cosine similarity between two player vectors."""
        # Convert to numpy arrays
        v1 = np.array(vector1).reshape(1, -1)
        v2 = np.array(vector2).reshape(1, -1)
        
        # Handle zero vectors
        if np.all(v1 == 0) or np.all(v2 == 0):
            return 0.0
        
        # Compute cosine similarity
        similarity = cosine_similarity(v1, v2)[0][0]
        return similarity
    
    def compute_euclidean_distance(self, vector1: List[float], vector2: List[float]) -> float:
        """Compute normalized Euclidean distance between two player vectors."""
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # Compute Euclidean distance
        distance = np.linalg.norm(v1 - v2)
        
        # Normalize by maximum possible distance (considering percentages 0-100)
        max_distance = np.sqrt(len(vector1) * (100 ** 2))
        normalized_distance = distance / max_distance
        
        # Convert to similarity (1 - distance)
        similarity = 1 - normalized_distance
        return max(0, similarity)
    
    def find_most_similar_player(self, 
                                target_player: str,
                                player_data: Dict[str, Dict[str, float]],
                                method: str = 'cosine',
                                exclude_self: bool = True) -> Tuple[str, float]:
        """Find the most similar player to the target player."""
        
        if target_player not in player_data:
            raise ValueError(f"Target player '{target_player}' not found in player data")
        
        # Normalize all player data
        normalized_data = self.normalize_player_data(player_data)
        target_vector = normalized_data[target_player]
        
        similarities = []
        
        for player_name, player_vector in normalized_data.items():
            # Skip self if requested
            if exclude_self and player_name == target_player:
                continue
            
            # Compute similarity based on method
            if method == 'cosine':
                similarity = self.compute_cosine_similarity(target_vector, player_vector)
            elif method == 'euclidean':
                similarity = self.compute_euclidean_distance(target_vector, player_vector)
            else:
                raise ValueError(f"Unknown similarity method: {method}")
            
            similarities.append((player_name, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if not similarities:
            return "No similar players found", 0.0
        
        return similarities[0]
    
    def find_top_similar_players(self, 
                                target_player: str,
                                player_data: Dict[str, Dict[str, float]],
                                top_n: int = 5,
                                method: str = 'cosine',
                                exclude_self: bool = True) -> List[Tuple[str, float]]:
        """Find the top N most similar players to the target player."""
        
        if target_player not in player_data:
            raise ValueError(f"Target player '{target_player}' not found in player data")
        
        # Normalize all player data
        normalized_data = self.normalize_player_data(player_data)
        target_vector = normalized_data[target_player]
        
        similarities = []
        
        for player_name, player_vector in normalized_data.items():
            # Skip self if requested
            if exclude_self and player_name == target_player:
                continue
            
            # Compute similarity based on method
            if method == 'cosine':
                similarity = self.compute_cosine_similarity(target_vector, player_vector)
            elif method == 'euclidean':
                similarity = self.compute_euclidean_distance(target_vector, player_vector)
            else:
                raise ValueError(f"Unknown similarity method: {method}")
            
            similarities.append((player_name, similarity))
        
        # Sort by similarity (highest first) and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def create_similarity_matrix(self, 
                                player_data: Dict[str, Dict[str, float]],
                                method: str = 'cosine') -> Tuple[np.ndarray, List[str]]:
        """Create a similarity matrix for all players."""
        
        # Normalize all player data
        normalized_data = self.normalize_player_data(player_data)
        player_names = list(normalized_data.keys())
        
        # Create matrix
        n_players = len(player_names)
        similarity_matrix = np.zeros((n_players, n_players))
        
        for i, player1 in enumerate(player_names):
            for j, player2 in enumerate(player_names):
                if i == j:
                    similarity_matrix[i][j] = 1.0  # Self-similarity
                else:
                    vector1 = normalized_data[player1]
                    vector2 = normalized_data[player2]
                    
                    if method == 'cosine':
                        similarity = self.compute_cosine_similarity(vector1, vector2)
                    elif method == 'euclidean':
                        similarity = self.compute_euclidean_distance(vector1, vector2)
                    else:
                        raise ValueError(f"Unknown similarity method: {method}")
                    
                    similarity_matrix[i][j] = similarity
        
        return similarity_matrix, player_names
    
    def analyze_player_profile(self, 
                              player_data: Dict[str, float]) -> Dict[str, any]:
        """Analyze a player's shooting profile characteristics."""
        
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'overall_average': 0.0,
            'consistency': 0.0,
            'three_point_specialist': False,
            'paint_presence': False,
            'well_rounded': False
        }
        
        # Get all non-zero percentages
        percentages = [v for v in player_data.values() if v > 0]
        
        if not percentages:
            return analysis
        
        overall_avg = np.mean(percentages)
        analysis['overall_average'] = overall_avg
        
        # Calculate consistency (lower standard deviation = more consistent)
        if len(percentages) > 1:
            std_dev = np.std(percentages)
            # Normalize consistency score (higher = more consistent)
            analysis['consistency'] = max(0, 100 - std_dev)
        
        # Identify strengths and weaknesses
        for zone, percentage in player_data.items():
            if percentage > overall_avg + 10:
                analysis['strengths'].append(zone)
            elif percentage > 0 and percentage < overall_avg - 10:
                analysis['weaknesses'].append(zone)
        
        # Identify playing style
        three_point_zones = ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Above Break 3']
        three_point_avg = np.mean([player_data.get(zone, 0) for zone in three_point_zones])
        
        paint_percentage = player_data.get('Paint', 0)
        
        analysis['three_point_specialist'] = three_point_avg > overall_avg + 5
        analysis['paint_presence'] = paint_percentage > overall_avg + 10
        analysis['well_rounded'] = len(analysis['weaknesses']) <= 2 and analysis['consistency'] > 70
        
        return analysis


class PlayerDatabase:
    """Simple database to store and retrieve player shooting data."""
    
    def __init__(self, db_file: str = "player_database.json"):
        self.db_file = db_file
        self.data = self.load_database()
    
    def load_database(self) -> Dict[str, Dict[str, float]]:
        """Load player data from JSON file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_database(self):
        """Save player data to JSON file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            print(f"Warning: Could not save database to {self.db_file}")
    
    def add_player(self, player_name: str, zone_data: Dict[str, float]):
        """Add a player to the database."""
        self.data[player_name] = zone_data
        self.save_database()
    
    def get_player(self, player_name: str) -> Optional[Dict[str, float]]:
        """Get a player's data from the database."""
        return self.data.get(player_name)
    
    def get_all_players(self) -> Dict[str, Dict[str, float]]:
        """Get all players from the database."""
        return self.data.copy()
    
    def remove_player(self, player_name: str):
        """Remove a player from the database."""
        if player_name in self.data:
            del self.data[player_name]
            self.save_database()


if __name__ == "__main__":
    # Test the similarity finder
    finder = PlayerSimilarityFinder()
    
    # Sample player data
    sample_players = {
        "Player A": {
            'Left Corner 3': 45.0, 'Left Wing 3': 38.0, 'Top of Key 3': 35.0,
            'Right Wing 3': 42.0, 'Right Corner 3': 48.0, 'Above Break 3': 33.0,
            'Left Mid Range': 52.0, 'Free Throw Line': 65.0, 'Right Mid Range': 48.0, 'Paint': 72.0
        },
        "Player B": {
            'Left Corner 3': 40.0, 'Left Wing 3': 35.0, 'Top of Key 3': 32.0,
            'Right Wing 3': 38.0, 'Right Corner 3': 45.0, 'Above Break 3': 30.0,
            'Left Mid Range': 50.0, 'Free Throw Line': 68.0, 'Right Mid Range': 45.0, 'Paint': 75.0
        },
        "Player C": {
            'Left Corner 3': 25.0, 'Left Wing 3': 28.0, 'Top of Key 3': 22.0,
            'Right Wing 3': 30.0, 'Right Corner 3': 28.0, 'Above Break 3': 20.0,
            'Left Mid Range': 35.0, 'Free Throw Line': 45.0, 'Right Mid Range': 38.0, 'Paint': 85.0
        }
    }
    
    # Find most similar player
    most_similar, similarity_score = finder.find_most_similar_player("Player A", sample_players)
    print(f"Most similar to Player A: {most_similar} (similarity: {similarity_score:.3f})")
    
    # Find top similar players
    top_similar = finder.find_top_similar_players("Player A", sample_players, top_n=2)
    print(f"Top similar players to Player A: {top_similar}")
    
    # Analyze player profile
    analysis = finder.analyze_player_profile(sample_players["Player A"])
    print(f"Player A analysis: {analysis}") 