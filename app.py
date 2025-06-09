import logging
from typing import Any, Tuple

import pandas as pd
import streamlit as st
from openai import OpenAI

from retrieval import FootballStatsRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state for caching
if "llm_cache" not in st.session_state:
    st.session_state.llm_cache = {}
if "retriever" not in st.session_state:
    st.session_state.retriever = None


@st.cache_data
def load_data():
    """Load and cache CSV data"""
    try:
        df = pd.read_csv("gw38.csv")
        return df
    except FileNotFoundError:
        st.error("CSV file not found!")
        return None
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None


@st.cache_resource
def initialize_openai_client():
    """Initialize and cache OpenAI client"""
    try:
        api_key = st.secrets["OPENAI_API_KEY"].strip()
        return OpenAI(api_key=api_key)
    except KeyError:
        st.error("OpenAI API key not found in secrets. Please configure OPENAI_API_KEY.")
        return None
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None


def get_cached_llm_response(cache_key: str, llm_function, *args, **kwargs):
    """Cache LLM responses to reduce API calls"""
    if cache_key in st.session_state.llm_cache:
        return st.session_state.llm_cache[cache_key]

    response = llm_function(*args, **kwargs)
    st.session_state.llm_cache[cache_key] = response
    return response


class StatsAssistant:
    def __init__(self, client: OpenAI, retriever: FootballStatsRetriever):
        self.client = client
        self.retriever = retriever

        # Stat mapping
        self.stat_mapping = {
            "total goals": ("goals", False),
            "goals per 90": ("goals", True),
            "total assists": ("assists", False),
            "assists per 90": ("assists", True),
            "possession": ("possession", False),
            "expected goals": ("expected_goals", False),
            "expected goals per 90": ("expected_goals", True),
            "yellow cards": ("yellow_cards", False),
            "red cards": ("red_cards", False),
        }

    def classify_question(self, question: str) -> str:
        """Question classification with prompting"""
        cache_key = f"classify_{hash(question)}"

        def _classify():
            system_prompt = """You are a football statistics classifier. Analyze user questions and map them to ONE of these exact categories:

VALID CATEGORIES:
- total goals
- goals per 90
- total assists  
- assists per 90
- possession
- expected goals
- expected goals per 90
- yellow cards
- red cards

RULES:
1. Look for keywords: "per 90", "per game", "rate" indicate per-90 stats
2. "Goals" maps to "total goals" (unless per-90 specified)
3. "Assists" maps to "total assists" (unless per-90 specified)
4. "xG", "expected goals" maps to "expected goals"
5. "Possession", "ball possession" maps to "possession"
6. "Yellow cards", "bookings" maps to "yellow cards"
7. "Red cards", "sent off" maps to "red cards"
8. If unclear or not about these stats, return "unknown"

ONLY respond with ONE of the valid categories or "unknown"."""

            user_prompt = f"Classify this question: '{question}'"

            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0,
                    max_tokens=20,
                )
                return response.choices[0].message.content.strip().lower()
            except Exception as e:
                logger.error(f"Error in question classification: {str(e)}")
                return "unknown"

        return get_cached_llm_response(cache_key, _classify)

    def route_question(self, question: str, team_name: str) -> Tuple[str, Any]:
        """Routing with error handling"""
        stat_intent = self.classify_question(question)

        if stat_intent in self.stat_mapping:
            stat_type, per_90 = self.stat_mapping[stat_intent]
            try:
                value = self.retriever.get_stat(team_name, stat_type, per_90)
                return stat_intent, value
            except Exception as e:
                return None, f"Error retrieving data: {str(e)}"
        else:
            return (
                None,
                f"Sorry, I can only answer questions about: {', '.join(self.stat_mapping.keys())}",
            )

    def generate_answer(self, question: str, field: str, value: Any, team_name: str) -> str:
        """Generate contextual answer with prompting"""
        cache_key = f"answer_{hash(question + str(value) + team_name)}"

        def _generate():
            system_prompt = """You are an expert football statistics assistant. Provide clear, engaging answers about team performance.

GUIDELINES:
1. Always mention the team name
2. Put the statistic in context (e.g., "This is quite high/low for a Premier League team")
3. Be conversational and friendly
4. If it's a per-90 stat, mention it normalizes for playing time
5. Keep responses concise but informative
6. Use football terminology appropriately
7. Respond in 1 or 2 lines max."""

            user_prompt = f"""
Question: {question}
Team: {team_name}
Statistic: {field}
Value: {value}

Generate a clear, engaging response."""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=150,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating answer: {str(e)}")
                return f"Based on the data, {team_name}'s {field} is {value}."

        return get_cached_llm_response(cache_key, _generate)


def main():
    st.set_page_config(page_title="EPL Stats Assistant", page_icon="⚽", layout="wide")

    st.title("EPL Stats Assistant")
    st.markdown(
        "Ask questions about English Premier League team statistics for the 2024/25 season!"
    )

    # Load data and initialize components
    df = load_data()
    client = initialize_openai_client()

    if df is None or client is None:
        st.stop()

    # Initialize retriever
    if st.session_state.retriever is None:
        try:
            st.session_state.retriever = FootballStatsRetriever(df)
        except Exception as e:
            st.error(f"Error initializing stats retriever: {str(e)}")
            st.stop()

    retriever = st.session_state.retriever
    assistant = StatsAssistant(client, retriever)

    # Sidebar with team info
    with st.sidebar:
        st.subheader("Available Stats (only team stats)")
        st.write("• Goals (total & per 90)")
        st.write("• Assists (total & per 90)")
        st.write("• Expected Goals (total & per 90)")
        st.write("• Possession %")
        st.write("• Yellow Cards")
        st.write("• Red Cards")

    # Main interface
    col1, col2 = st.columns([2, 1])

    teams = retriever.get_available_teams()
    with col1:
        # Team selection with search
        team_name = st.selectbox("Select Team", teams, help="Choose a team to analyze")

        # Question input with examples
        question = st.text_input(
            "Ask a question about this team",
            placeholder="e.g., 'How many goals did Arsenal score?' or 'What's Liverpool's possession per game?'",
            help="Ask about goals, assists, expected goals, possession, or cards",
        )

        show_details = st.checkbox("Show classification details")

    with col2:
        st.subheader("Quick Season Stats")
        if team_name:
            summary = retriever.get_team_summary(team_name)
            if "error" not in summary:
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    st.metric("Goals", summary["goals"])
                with metric_cols[1]:
                    st.metric("Assists", summary["assists"])
                with metric_cols[2]:
                    st.metric("Possession %", f"{summary['possession']}%")

    action_col1, action_col2 = st.columns(spec=[1, 1])

    with action_col1:
        get_answer_clicked = st.button("Get Answer", type="primary")

    with action_col2:
        clear_cache_clicked = st.button("Clear Cache")

    if clear_cache_clicked:
        st.session_state.llm_cache.clear()
        st.success("Cache cleared!")

    if get_answer_clicked:
        if not team_name or not question:
            st.error("Please select a team and enter a question.")
            st.stop()

        with st.spinner("Analyzing question and retrieving data..."):
            try:
                # Route question and get answer
                field, value = assistant.route_question(question, team_name)

                if field:
                    answer = assistant.generate_answer(question, field, value, team_name)
                    st.success(answer)

                else:
                    st.warning(value)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error processing question: {str(e)}")


if __name__ == "__main__":
    main()
