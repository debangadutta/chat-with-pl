# app.py

import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
from retrieval import (
    total_goals_scored, total_assists, possession,
    expected_goals, yellow_cards, red_cards
)

# Load environment variables
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Load CSV
df = pd.read_csv("gw38.csv")  # make sure your CSV is in same folder

# NEW: LLM-guided route_question
def classify_question(question):
    system_prompt = """
You are an assistant that maps user questions about football team stats to one of the following known stats:
- total goals
- assists
- possession
- expected goals
- yellow cards
- red cards

If the question does not match any of these, respond with "unknown".

Only return one of: [total goals, assists, possession, expected goals, yellow cards, red cards, unknown].
"""

    user_prompt = f"User question: {question}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    stat_intent = response.choices[0].message.content.strip().lower()
    return stat_intent

# Main routing using classified intent
def route_question(question, df, team_name):
    stat_intent = classify_question(question)

    if stat_intent == "total goals":
        return "Total goals", total_goals_scored(df, team_name)
    elif stat_intent == "assists":
        return "Total assists", total_assists(df, team_name)
    elif stat_intent == "possession":
        return "Possession %", possession(df, team_name)
    elif stat_intent == "expected goals":
        return "Expected Goals", expected_goals(df, team_name)
    elif stat_intent == "yellow cards":
        return "Yellow cards", yellow_cards(df, team_name)
    elif stat_intent == "red cards":
        return "Red cards", red_cards(df, team_name)
    else:
        return None, "Sorry, I cannot answer that question based on available team stats."

# Call LLM to generate answer
def call_llm(question, field, value, team_name):
    system_prompt = "You are an expert football data assistant. Answer questions based on provided data."

    user_prompt = f"""
User question: {question}
Retrieved data: {field} for {team_name} = {value}

Please generate a clear and friendly answer for the user.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content

# Streamlit App UI
st.title("🏆 EPL Stats Assistant")

# Team selection
team_list = df['Squad'].tolist()
team_name = st.selectbox("Select Team", team_list)

# User question input
question = st.text_input("Ask a question about this team (e.g. 'How many goals did Chelsea score?')")

# Submit button
if st.button("Submit"):
    if team_name and question:
        field, value = route_question(question, df, team_name)

        if field:
            answer = call_llm(question, field, value, team_name)
            st.success(answer)
        else:
            st.warning(value)
    else:
        st.error("Please select a team and enter a question.")
