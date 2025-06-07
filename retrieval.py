def clean_minutes(minutes_str):
    """Helper to convert '3,420' string to int 3420"""
    return int(minutes_str.replace(',', ''))

def total_goals_scored(df, team_name, per_90=False):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."

    total_goals = row['Gls'].values[0]
    minutes_played = clean_minutes(row['Min'].values[0])

    if per_90:
        return round((total_goals / minutes_played) * 90, 2)
    else:
        return total_goals

def total_assists(df, team_name, per_90=False):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."

    total_assists = row['Ast'].values[0]
    minutes_played = clean_minutes(row['Min'].values[0])

    if per_90:
        return round((total_assists / minutes_played) * 90, 2)
    else:
        return total_assists

def possession(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return row['Poss'].values[0]

def expected_goals(df, team_name, per_90=False):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."

    total_xg = row['xG'].values[0]
    minutes_played = clean_minutes(row['Min'].values[0])

    if per_90:
        return round((total_xg / minutes_played) * 90, 2)
    else:
        return total_xg

def yellow_cards(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return row['CrdY'].values[0]

def red_cards(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return row['CrdR'].values[0]
