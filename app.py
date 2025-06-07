import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from retrieval import (
    total_goals_scored, total_assists, possession,
    expected_goals, yellow_cards, red_cards
)

# Load OpenAI API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Load CSV
df = pd.read_csv("gw38.csv")

# NEW: LLM-guided classify_question
def classify_question(question):
    system_prompt = """
You are an assistant that maps user questions about football team stats to one of the following known stats:
- total goals
- total goals per 90
- assists
- assists per 90
- possession
- expected goals
- expected goals per 90
- yellow cards
- red cards

If the question does not match any of these, respond with "unknown".

Only return one of: [total goals, total goals per 90, assists, assists per 90, possession, expected goals, expected goals per 90, yellow cards, red cards, unknown].
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

# Main routing
def route_question(question, df, team_name):
    stat_intent = classify_question(question)

    if stat_intent == "total goals":
        return stat_intent, total_goals_scored(df, team_name)
    elif stat_intent == "total goals per 90":
        return stat_intent, total_goals_scored(df, team_name, per_90=True)
    elif stat_intent == "assists":
        return stat_intent, total_assists(df, team_name)
    elif stat_intent == "assists per 90":
        return stat_intent, total_assists(df, team_name, per_90=True)
    elif stat_intent == "possession":
        return stat_intent, possession(df, team_name)
    elif stat_intent == "expected goals":
        return stat_intent, expected_goals(df, team_name)
    elif stat_intent == "expected goals per 90":
        return stat_intent, expected_goals(df, team_name, per_90=True)
    elif stat_intent == "yellow cards":
        return stat_intent, yellow_cards(df, team_name)
    elif stat_intent == "red cards":
        return stat_intent, red_cards(df, team_name)
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
question = st.text_input("Ask a question about this team (e.g. 'How many goals did Arsenal score per 90?')")

# Optional toggle to show intent and retrieved value
show_details = st.checkbox("Show intent and retrieved value")

# Submit button
if st.button("Submit"):
    if team_name and question:
        field, value = route_question(question, df, team_name)

        if field:
            answer = call_llm(question, field, value, team_name)
            st.success(answer)

            # If user enabled details → show them
            if show_details:
                st.info(f"LLM classified this as: **{field}**\n\nRetrieved value: **{value}**")
        else:
            st.warning(value)
    else:
        st.error("Please select a team and enter a question.")
