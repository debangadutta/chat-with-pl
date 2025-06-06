# app.py

import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
from retrieval import total_goals_scored, total_assists, possession, expected_goals

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Load CSV
df = pd.read_csv("gw38.csv")  # make sure your CSV is in same folder

# Route question to correct retrieval function
def route_question(question, df, team_name):
    question_lower = question.lower()

    if "goal" in question_lower:
        value = total_goals_scored(df, team_name)
        field = "Total goals"
    elif "assist" in question_lower:
        value = total_assists(df, team_name)
        field = "Total assists"
    elif "possession" in question_lower:
        value = possession(df, team_name)
        field = "Possession %"
    elif "expected goals" in question_lower or "xg" in question_lower:
        value = expected_goals(df, team_name)
        field = "Expected Goals"
    else:
        return None, "I don't know how to answer that yet."
    
    return field, value

# Call LLM (GPT-3.5)
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
st.title("🏆 EPL Stats Assistant (RAG + LLM Demo)")

# Team selection
team_list = df['Squad'].tolist()
team_name = st.selectbox("Select Team", team_list)

# User question input
question = st.text_input("Ask a question about this team (e.g. 'How many goals did Arsenal score?')")

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
