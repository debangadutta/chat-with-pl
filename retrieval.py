def total_goals_scored(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return round(row['Gls'].values[0]*38)

def total_assists(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return round(row['Ast'].values[0]*38)

def possession(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return row['Poss'].values[0]

def expected_goals(df, team_name):
    row = df[df['Squad'] == team_name]
    if row.empty:
        return f"Team '{team_name}' not found."
    return row['xG'].values[0]

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
