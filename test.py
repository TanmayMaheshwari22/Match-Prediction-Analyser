import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.football-data.org/v4"
api_key = os.environ.get('FOOTBALL_API_KEY')
headers = {"X-Auth-Token": api_key}


def get_team_id(team_name: str) -> int:
    """Find team ID from World Cup 2026 teams list."""
    url = f"{BASE_URL}/competitions/WC/teams"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    for team in data.get("teams", []):
        if team_name.lower() in team["name"].lower():
            return team["id"]
    return None


def get_stats(team_name: str) -> str:
    """Get last 5 match results for a team in the World Cup."""
    team_id = get_team_id(team_name)
    if not team_id:
        return json.dumps({"error": f"Team '{team_name}' not found"})

    # Get all finished matches for this team (no limit param on free tier)
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {
        "status": "FINISHED",
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    all_matches = data.get("matches", [])

    # Take the last 5
    matches = all_matches[-5:] if len(all_matches) > 5 else all_matches

    if not matches:
        return json.dumps({"error": f"No finished matches found for '{team_name}'"})

    results = []
    total_goals_scored = 0
    total_goals_conceded = 0
    form = []

    for match in matches:
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        home_goals = match["score"]["fullTime"]["home"]
        away_goals = match["score"]["fullTime"]["away"]

        is_home = match["homeTeam"]["id"] == team_id
        goals_scored = home_goals if is_home else away_goals
        goals_conceded = away_goals if is_home else home_goals

        total_goals_scored += goals_scored
        total_goals_conceded += goals_conceded

        if goals_scored > goals_conceded:
            form.append("W")
        elif goals_scored == goals_conceded:
            form.append("D")
        else:
            form.append("L")

        opponent = away_team if is_home else home_team
        results.append({
            "opponent": opponent,
            "score": f"{goals_scored}-{goals_conceded}",
            "result": form[-1],
            "date": match["utcDate"][:10],
            "competition": match["competition"]["name"],
        })

    stats = {
        "team": team_name,
        "matches_played": len(matches),
        "form": "-".join(form),
        "total_goals_scored": total_goals_scored,
        "total_goals_conceded": total_goals_conceded,
        "results": results,
    }
    return json.dumps(stats)


# Quick test
if __name__ == "__main__":
    result = get_stats("Portugal")
    print(json.dumps(json.loads(result), indent=2))
