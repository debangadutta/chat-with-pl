import pandas as pd
from typing import Union, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballStatsRetriever:
    """Football statistics retrieval with error handling and caching"""
    
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._cache = {}
        # Mapping of stat types to column names
        self.stat_columns = {
            'goals': 'Gls',
            'assists': 'Ast',
            'expected_goals': 'xG',
            'possession': 'Poss',
            'yellow_cards': 'CrdY',
            'red_cards': 'CrdR'
        }
    
    def _clean_minutes(self, minutes_str: Union[str, int, float]) -> int:
        """Helper to convert various minute formats to int"""
        if isinstance(minutes_str, (int, float)):
            return int(minutes_str)
        return int(str(minutes_str).replace(',', ''))
    
    def _get_team_row(self, team_name: str) -> pd.Series:
        """Get team row with caching and better error handling"""
        cache_key = f"team_row_{team_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Case-insensitive team search
        team_matches = self.df[self.df['Squad'].str.lower() == team_name.lower()]
        
        if team_matches.empty:
            # Try partial matching
            partial_matches = self.df[self.df['Squad'].str.contains(team_name, case=False, na=False)]
            if partial_matches.empty:
                raise ValueError(f"Team '{team_name}' not found. Available teams: {', '.join(self.df['Squad'].tolist())}")
            elif len(partial_matches) > 1:
                raise ValueError(f"Multiple teams match '{team_name}': {', '.join(partial_matches['Squad'].tolist())}")
            team_row = partial_matches.iloc[0]
        else:
            team_row = team_matches.iloc[0]
        
        self._cache[cache_key] = team_row
        return team_row
    
    def _calculate_per_90(self, value: float, minutes: int) -> float:
        """Calculate per-90 minute statistics"""
        if minutes <= 0:
            return 0.0
        return round((value / minutes) * 90, 2)
    
    def get_stat(self, team_name: str, stat_type: str, per_90: bool = False) -> Union[float, int, str]:
        """Generic method to get any statistic"""
        try:
            row = self._get_team_row(team_name)
            
            if stat_type not in self.stat_columns:
                raise ValueError(f"Unknown stat type: {stat_type}")
            
            column = self.stat_columns[stat_type]
            value = row[column]
            if value is None:
                raise ValueError(f"Column '{column}' not found in DataFrame")
            
            # Handle per-90 calculations (not applicable for possession and cards)
            if per_90 and stat_type in ['goals', 'assists', 'expected_goals']:
                minutes = self._clean_minutes(row['Min'])
                return self._calculate_per_90(value, minutes)
            
            return value
            
        except Exception as e:
            logger.error(f"Error retrieving {stat_type} for {team_name}: {str(e)}")
            return str(e)
    
    def get_multiple_stats(self, team_name: str, stat_types: List[str]) -> Dict[str, Any]:
        """Retrieve multiple statistics at once"""
        results = {}
        for stat_type in stat_types:
            results[stat_type] = self.get_stat(team_name, stat_type)
        return results
    
    def get_team_summary(self, team_name: str) -> Dict[str, Any]:
        """Get comprehensive team summary"""
        try:
            row = self._get_team_row(team_name)
            minutes = self._clean_minutes(row['Min'])
            
            return {
                'team': row['Squad'],
                'goals': row['Gls'],
                'goals_per_90': self._calculate_per_90(row['Gls'], minutes),
                'assists': row['Ast'],
                'assists_per_90': self._calculate_per_90(row['Ast'], minutes),
                'expected_goals': row['xG'],
                'expected_goals_per_90': self._calculate_per_90(row['xG'], minutes),
                'possession': row['Poss'],
                'yellow_cards': row['CrdY'],
                'red_cards': row['CrdR'],
                'minutes_played': minutes
            }
        except Exception as e:
            logger.error(f"Error getting summary for {team_name}: {str(e)}")
            return {'error': str(e)}
    
    def get_available_teams(self) -> List[str]:
        """Get list of all available teams"""
        return sorted(self.df['Squad'].tolist())

# Legacy function compatibility (optional - for backward compatibility)
def total_goals_scored(df, team_name, per_90=False):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'goals', per_90)

def total_assists(df, team_name, per_90=False):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'assists', per_90)

def possession(df, team_name):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'possession')

def expected_goals(df, team_name, per_90=False):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'expected_goals', per_90)

def yellow_cards(df, team_name):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'yellow_cards')

def red_cards(df, team_name):
    retriever = FootballStatsRetriever(df)
    return retriever.get_stat(team_name, 'red_cards')