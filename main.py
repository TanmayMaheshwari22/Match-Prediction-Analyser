import os
import json
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

load_dotenv()

tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


# --- Tools ---

@tool
def get_team_form(team_name: str) -> str:
    """Get the last 5 international match results for a football team including scores, opponents, and dates."""
    query = f"{team_name} national football team last 5 international match results scores 2026"

    response = tavily.search(
        query=query,
        search_depth="basic",
        include_answer=True,
        max_results=5,
    )

    answer = response.get("answer", "")
    return answer


@tool
def get_h2h(team_name1: str, team_name2: str) -> str:
    """Get the last 5 head-to-head matches played between two teams with scorelines."""
    query = f"Last 5 matches played and scoreline between {team_name1} and {team_name2}"

    response = tavily.search(
        query=query,
        search_depth="basic",
        include_answer=True,
        max_results=5,
    )

    answer = response.get("answer", "")
    return answer


@tool
def get_injuries(team_name: str) -> str:
    """Get the recent injuries in the team."""
    query = f"{team_name} national football team injuries World Cup 2026 squad"

    response = tavily.search(
        query=query,
        search_depth="basic",
        include_answer=True,
        max_results=5,
    )

    answer = response.get("answer", "")

    injury_keywords = ["injury", "injured", "ruled out", "doubtful", "miss", "sidelined", "hamstring", "knee"]

    if not any(keyword in answer.lower() for keyword in injury_keywords):
        return f"No major injuries reported for {team_name}. Squad appears fully fit. Additional context: {answer}"

    return answer


@tool
def get_expert_predictions(team_name1: str, team_name2: str) -> str:
    """Get expert predictions and analysis for the match between two teams."""
    query = f"{team_name1} vs {team_name2} expert prediction analysis World Cup 2026"

    response = tavily.search(
        query=query,
        search_depth="basic",
        include_answer=True,
        max_results=5,
    )

    answer = response.get("answer", "")
    return answer


# --- Pydantic Output Schema ---

class MatchPrediction(BaseModel):
    team_a: str = Field(description="First team name")
    team_b: str = Field(description="Second team name")
    predicted_winner: str = Field(description="Predicted winner or 'Draw'")
    predicted_score: str = Field(description="Predicted scoreline, e.g. '2-1'")
    confidence: float = Field(description="Confidence level between 0.0 and 1.0")
    key_factors: list[str] = Field(description="Key factors influencing the prediction")


# --- Agent Setup ---

tools = [get_team_form, get_h2h, get_injuries, get_expert_predictions]

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

system_prompt = """You are a football match prediction expert. Given two teams, you must:

1. Use get_team_form for EACH team to get their recent form
2. Use get_h2h to get head-to-head history between the two teams
3. Use get_injuries for EACH team to check squad fitness
4. Use get_expert_predictions to get expert analysis for the match

After gathering all data, provide your prediction with:
- Predicted winner (or Draw)
- Predicted scoreline
- Confidence level (0.0 to 1.0)
- Key factors that influenced your prediction

Use expert predictions as one input alongside your own analysis. Don't simply agree with experts — weigh their views against the stats and form data."""

agent = create_react_agent(llm, tools, prompt=system_prompt)


# --- Run ---

if __name__ == "__main__":
    user_input = "Who will win the match between Portugal and Uzbekistan?"

    response = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    # Print the final response
    final_message = response["messages"][-1]
    print(final_message.content)
