import pandas as pd

# Load your CSV
df = pd.read_csv("gw38.csv")

# Display first rows
# print(df.head())

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


if __name__=="__main__":
    team = "Chelsea"
    print(f"Team: {team}")
    print("Total goals:", total_goals_scored(df, team))
    print("Total assists:", total_assists(df, team))
    print("Possession %:", possession(df, team))
    print("Expected Goals per 90:", expected_goals(df, team))

