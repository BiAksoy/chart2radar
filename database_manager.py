import streamlit as st
import sqlite3
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
import os

class SQLitePlayerDatabase:
    """SQLite-based persistent database for player shooting data."""
    
    def __init__(self, db_path: str = "basketball_players.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection using Streamlit's connection API."""
        return st.connection('basketball_db', type='sql', url=f'sqlite:///{self.db_path}')
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            # Create database file if it doesn't exist
            if not os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.close()
            
            # Use raw connection for table creation
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    percentages TEXT NOT NULL,
                    made_shots TEXT,
                    attempts TEXT,
                    games_played INTEGER DEFAULT 44,
                    original_games INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_name ON players(name)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database initialization error: {e}")
    
    def add_player(self, player_name: str, percentages: Dict[str, float], 
                   made_shots: Optional[Dict[str, int]] = None, 
                   attempts: Optional[Dict[str, int]] = None,
                   games_played: int = 44,
                   original_games: Optional[int] = None):
        """Add or update a player in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert dicts to JSON strings
            percentages_json = json.dumps(percentages)
            made_shots_json = json.dumps(made_shots or {})
            attempts_json = json.dumps(attempts or {})
            original_games = original_games or games_played
            
            # Use INSERT OR REPLACE to handle both new and existing players
            cursor.execute('''
                INSERT OR REPLACE INTO players 
                (name, percentages, made_shots, attempts, games_played, original_games, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (player_name, percentages_json, made_shots_json, attempts_json, 
                  games_played, original_games))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Error adding player {player_name}: {e}")
            return False
    
    def get_player(self, player_name: str) -> Optional[Dict[str, any]]:
        """Get a player's complete data from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM players WHERE name = ?', (player_name,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'percentages': json.loads(row[2]),
                    'made_shots': json.loads(row[3]) if row[3] else {},
                    'attempts': json.loads(row[4]) if row[4] else {},
                    'games_played': row[5],
                    'original_games': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            return None
            
        except Exception as e:
            st.error(f"Error getting player {player_name}: {e}")
            return None
    
    def get_player_percentages(self, player_name: str) -> Optional[Dict[str, float]]:
        """Get a player's percentage data."""
        player_data = self.get_player(player_name)
        return player_data['percentages'] if player_data else None
    
    def get_player_made_shots(self, player_name: str) -> Optional[Dict[str, int]]:
        """Get a player's made shots data."""
        player_data = self.get_player(player_name)
        return player_data['made_shots'] if player_data else None
    
    def get_player_games_played(self, player_name: str) -> Optional[int]:
        """Get a player's games played."""
        player_data = self.get_player(player_name)
        return player_data['games_played'] if player_data else None
    
    def get_player_original_games(self, player_name: str) -> Optional[int]:
        """Get a player's original games played."""
        player_data = self.get_player(player_name)
        return player_data['original_games'] if player_data else None
    
    def get_all_players(self) -> Dict[str, Dict[str, float]]:
        """Get all players' percentage data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name, percentages FROM players ORDER BY name')
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for row in rows:
                result[row[0]] = json.loads(row[1])
            
            return result
            
        except Exception as e:
            st.error(f"Error getting all players: {e}")
            return {}
    
    def get_all_players_made_shots(self) -> Dict[str, Dict[str, int]]:
        """Get all players' made shots data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name, made_shots FROM players WHERE made_shots IS NOT NULL ORDER BY name')
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for row in rows:
                if row[1]:  # Check if made_shots is not empty
                    result[row[0]] = json.loads(row[1])
            
            return result
            
        except Exception as e:
            st.error(f"Error getting all players made shots: {e}")
            return {}
    
    def remove_player(self, player_name: str) -> bool:
        """Remove a player from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM players WHERE name = ?', (player_name,))
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            st.error(f"Error removing player {player_name}: {e}")
            return False
    
    def clear_database(self) -> bool:
        """Clear all players from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM players')
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Error clearing database: {e}")
            return False
    
    def get_player_count(self) -> int:
        """Get total number of players in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM players')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            st.error(f"Error getting player count: {e}")
            return 0
    
    def get_recent_players(self, limit: int = 5) -> List[str]:
        """Get recently added/updated players."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM players ORDER BY updated_at DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            st.error(f"Error getting recent players: {e}")
            return []
    
    @staticmethod
    def scale_stats_to_games(made_shots: Dict[str, int], attempts: Dict[str, int], 
                           original_games: int, target_games: int = 44) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Scale made shots and attempts from original games to target games."""
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
        return self.add_player(
            player_name, 
            percentages, 
            scaled_made, 
            scaled_attempts, 
            target_games, 
            original_games
        )
    
    def get_database_stats(self) -> Dict[str, any]:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total players
            cursor.execute('SELECT COUNT(*) FROM players')
            total_players = cursor.fetchone()[0]
            
            # Get most recent player
            cursor.execute('SELECT name, updated_at FROM players ORDER BY updated_at DESC LIMIT 1')
            recent_result = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_players': total_players,
                'most_recent_player': recent_result[0] if recent_result else None,
                'last_updated': recent_result[1] if recent_result else None,
                'database_path': self.db_path
            }
            
        except Exception as e:
            st.error(f"Error getting database stats: {e}")
            return {'total_players': 0, 'most_recent_player': None, 'last_updated': None}


# Backward compatibility: alias for the old class name
PlayerDatabase = SQLitePlayerDatabase 