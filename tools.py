import csv
from pathlib import Path
from typing import Any

import requests
from dotenv import dotenv_values

config = dotenv_values(Path(__file__).with_name(".env"))
api_request_url = "https://www.omdbapi.com/"
movies_file_path = Path(__file__).parent / "data" / "movies.csv"


def require_config_value(name):
    value = config.get(name)
    if not value or not value.strip():
        raise Exception(f"You must provide {name} in .env file, see example in .env.example file")
    return value.strip()


omdb_api_key = require_config_value("OMDB_API_KEY")


def group_csv_by(file_path: Path, column: str) -> dict[str, list[dict[str, Any]]]:
    grouped = {}

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise ValueError(f"Column '{column}' does not exist in the CSV file")

        for row in reader:
            genres = row[column].split(",")
            for genre in genres:
                key = genre.strip().lower()
                if not key:
                    continue

                if key not in grouped:
                    grouped[key] = [row]
                else:
                    grouped[key].append(row)

    return grouped


movies_by_genre = group_csv_by(movies_file_path, "Genre")


def get_movie_info(title, year=None):
    if not omdb_api_key:
        return {"error": "OMDB_API_KEY environment variable is not set"}

    try:
        params = {
            "t": title,
            "plot": "full",
            "apikey": omdb_api_key
        }
        if year:
            params["y"] = year
        response = requests.get(api_request_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return {"error": str(exc)}


def get_list_of_movies_by_genre(genre, k="3"):
    if genre.lower() not in movies_by_genre:
        return {"error": "invalid genre"}
    try:
        limit = int(k)
    except ValueError:
        return {"error": "k must be an integer"}
    if limit <= 0:
        return {"error": "k must be a positive integer"}
    return movies_by_genre[genre.lower()][:limit]


def get_list_of_genres():
    return list(movies_by_genre.keys())


def get_newest_movie(movie1, movie2):
    try:
        year1 = int(movie1["Year"])
        year2 = int(movie2["Year"])

        return "movie1 is newer" if year1 > year2 else "movie2 is newer" if year2 > year1 else "they are same age"
    except Exception as ex:
        return {"error": f"movies does not contain release year {ex}"}

tool_map = {
    "get_movie_info": get_movie_info,
    "get_list_of_movies_by_genre": get_list_of_movies_by_genre,
    "get_list_of_genres": get_list_of_genres,
    "get_newest_movie": get_newest_movie
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_movie_info",
            "description": "Get movie by title and year",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of a movie"
                    },
                    "year": {
                        "type": "string",
                        "description": "Release year of a movie"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_list_of_movies_by_genre",
            "description": "use this tool when user asks to search by genre, it must return only top n movies",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "Genre of movie"
                    },
                    "k": {
                        "type": "string",
                        "description": "get only top k movies"
                    }
                },
                "required": ["genre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_list_of_genres",
            "description": "use this tool if user asks for list of all possible genres, or if user uses wrong genre for search by genre tool",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_newest_movie",
            "description": "Use this tool when the user asks to identify newest movie by release year",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie1": {
                        "type": "object",
                        "description": "First movie information"
                    },
                    "movie2": {
                        "type": "object",
                        "description": "Second movie information"
                    }
                },
                "required": ["movie1", "movie2"]
            }
        }
    }
]
