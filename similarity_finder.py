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
            'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint'
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
        three_point_zones = ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3']
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
    
    def load_database(self) -> Dict[str, Dict[str, any]]:
        """Load player data from JSON file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    # Convert old format to new format if needed
                    for player_name, player_data in data.items():
                        if 'percentages' not in player_data:
                            # Old format: convert to new format
                            data[player_name] = {
                                'percentages': player_data,
                                'made_shots': {},
                                'attempts': {}
                            }
                    return data
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
    
    def add_player(self, player_name: str, percentages: Dict[str, float], 
                   made_shots: Optional[Dict[str, int]] = None, 
                   attempts: Optional[Dict[str, int]] = None,
                   games_played: int = 44,
                   original_games: Optional[int] = None):
        """Add a player to the database with percentages, made shots, attempts, and games played."""
        self.data[player_name] = {
            'percentages': percentages,
            'made_shots': made_shots or {},
            'attempts': attempts or {},
            'games_played': games_played,
            'original_games': original_games or games_played
        }
        self.save_database()
    
    def get_player(self, player_name: str) -> Optional[Dict[str, any]]:
        """Get a player's data from the database."""
        return self.data.get(player_name)
    
    def get_player_percentages(self, player_name: str) -> Optional[Dict[str, float]]:
        """Get a player's percentage data (for backwards compatibility)."""
        player_data = self.data.get(player_name)
        if player_data:
            if 'percentages' in player_data:
                return player_data['percentages']
            else:
                # Old format
                return player_data
        return None
    
    def get_player_made_shots(self, player_name: str) -> Optional[Dict[str, int]]:
        """Get a player's made shots data."""
        player_data = self.data.get(player_name)
        if player_data and 'made_shots' in player_data:
            return player_data['made_shots']
        return None
    
    def get_player_games_played(self, player_name: str) -> Optional[int]:
        """Get a player's games played."""
        player_data = self.data.get(player_name)
        if player_data and 'games_played' in player_data:
            return player_data['games_played']
        return None
    
    def get_player_original_games(self, player_name: str) -> Optional[int]:
        """Get a player's original games played."""
        player_data = self.data.get(player_name)
        if player_data and 'original_games' in player_data:
            return player_data['original_games']
        return None
    
    def get_all_players(self) -> Dict[str, Dict[str, float]]:
        """Get all players percentage data (for backwards compatibility)."""
        result = {}
        for player_name, player_data in self.data.items():
            if 'percentages' in player_data:
                result[player_name] = player_data['percentages']
            else:
                # Old format
                result[player_name] = player_data
        return result
    
    def get_all_players_made_shots(self) -> Dict[str, Dict[str, int]]:
        """Get all players made shots data."""
        result = {}
        for player_name, player_data in self.data.items():
            if 'made_shots' in player_data:
                result[player_name] = player_data['made_shots']
        return result
    
    def remove_player(self, player_name: str):
        """Remove a player from the database."""
        if player_name in self.data:
            del self.data[player_name]
            self.save_database()
    
    @staticmethod
    def scale_stats_to_games(made_shots: Dict[str, int], attempts: Dict[str, int], 
                           original_games: int, target_games: int = 44) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Scale made shots and attempts from original games to target games (default 44)."""
        if original_games <= 0:
            return made_shots, attempts
        
        scale_factor = target_games / original_games
        
        scaled_made = {}
        scaled_attempts = {}
        
        for zone in made_shots:
            scaled_made[zone] = round(made_shots[zone] * scale_factor)
            
        for zone in attempts:
            scaled_attempts[zone] = round(attempts[zone] * scale_factor)
        
        return scaled_made, scaled_attempts
    
    def add_player_with_scaling(self, player_name: str, made_shots: Dict[str, int], 
                              attempts: Dict[str, int], original_games: int, 
                              target_games: int = 44):
        """Add a player with automatic scaling to target games."""
        # Scale the stats
        scaled_made, scaled_attempts = self.scale_stats_to_games(
            made_shots, attempts, original_games, target_games
        )
        
        # Calculate percentages
        percentages = {}
        for zone in scaled_made:
            if scaled_attempts.get(zone, 0) > 0:
                percentages[zone] = round((scaled_made[zone] / scaled_attempts[zone]) * 100, 1)
            else:
                percentages[zone] = 0.0
        
        # Add to database
        self.add_player(
            player_name, 
            percentages, 
            scaled_made, 
            scaled_attempts, 
            target_games, 
            original_games
        )


if __name__ == "__main__":
    # Test the similarity finder
    finder = PlayerSimilarityFinder()
    
    # Sample player data
    sample_players = {
        "Player A": {
            'Left Corner 3': 45.0, 'Left Wing 3': 38.0, 'Top of Key 3': 35.0,
            'Right Wing 3': 42.0, 'Right Corner 3': 48.0,
            'Left Mid Range': 52.0, 'Left Free Throw': 65.0, 'Right Free Throw': 68.0, 'Right Mid Range': 48.0, 'Paint': 72.0
        },
        "Player B": {
            'Left Corner 3': 40.0, 'Left Wing 3': 35.0, 'Top of Key 3': 32.0,
            'Right Wing 3': 38.0, 'Right Corner 3': 45.0,
            'Left Mid Range': 50.0, 'Left Free Throw': 68.0, 'Right Free Throw': 70.0, 'Right Mid Range': 45.0, 'Paint': 75.0
        },
        "Player C": {
            'Left Corner 3': 25.0, 'Left Wing 3': 28.0, 'Top of Key 3': 22.0,
            'Right Wing 3': 30.0, 'Right Corner 3': 28.0,
            'Left Mid Range': 35.0, 'Left Free Throw': 45.0, 'Right Free Throw': 47.0, 'Right Mid Range': 38.0, 'Paint': 85.0
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