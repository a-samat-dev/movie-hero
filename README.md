# Movie Tool-Calling Agent

This project is a small Python movie assistant that uses the OpenAI Chat Completions API with function tools.

It can:

- remember short-term conversation facts, such as the user's name
- fetch movie details from OMDb by title and optional year
- search a local IMDb CSV dataset by genre
- list available genres from the CSV
- compare two movie objects by release year
- summarize older conversation history when the message list grows too large

## Project Files

```text
agent.py         Main chat loop, OpenAI client, tool execution, and summary memory
tools.py         Tool definitions and tool implementations
data/movies.csv  Local movie dataset used for genre search
.env             Local secrets and runtime settings, not for sharing
.env.example     Safe template showing required environment variables
requirements.txt Python dependencies
```

## Requirements

- Python 3.10 or newer is recommended
- OpenAI API key
- OMDb API key
- Kaggle IMDb dataset saved as `data/movies.csv`

Install dependencies:

```bash
pip install -r requirements.txt
```

If your system has multiple Python versions, use:

```bash
python3 -m pip install -r requirements.txt
```

## Dataset Setup

Before running this project, download the IMDb dataset from Kaggle:

```text
https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows
```

After downloading it:

1. Extract the dataset archive if needed.
2. Rename the CSV file to `movies.csv`.
3. Put it inside the `data` folder.

Expected final path:

```text
data/movies.csv
```

The `data/movies.csv` file is ignored by git because it is a local downloaded dataset.

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
OMDB_API_KEY="your-omdb-api-key"
OPENAI_API_KEY="your-openai-api-key"
MAX_CYCLES=5
MAX_RECENT_MESSAGES=5
```

The code uses `dotenv_values(...)` instead of `load_dotenv()`. This means values are read directly from the local `.env` file and do not get mixed with your Mac/system environment variables.

Required values:

- `OPENAI_API_KEY`: API key for OpenAI
- `OMDB_API_KEY`: API key for OMDb
- `MAX_CYCLES`: maximum number of model/tool reasoning cycles per user prompt
- `MAX_RECENT_MESSAGES`: approximate number of recent messages to keep before summarizing older turns

Do not commit or share `.env`. Share `.env.example` instead.

## Running

Run the agent:

```bash
python3 agent.py
```

The script first runs the sample prompts in `start_chatting()`, then enters an interactive prompt loop.

To exit the loop, type:

```text
gandalf
```

## How The Agent Loop Works

The main loop is in `chat_agent(...)`.

For each user prompt:

1. The user message is appended to `conversation_history`.
2. The model receives the conversation and available tool schemas.
3. If the model returns normal text, the answer is printed and saved.
4. If the model returns one or more tool calls, each tool is executed.
5. Each tool result is appended as a `role: "tool"` message with the matching `tool_call_id`.
6. The model is called again with the tool results.
7. The cycle repeats until the model returns final text or `MAX_CYCLES` is reached.

This supports multi-tool calling because the code loops over all tool calls returned in a model response.

## Summary Memory

The agent keeps short-term memory in `conversation_history`.

When the history grows beyond `MAX_RECENT_MESSAGES`, `maybe_summarize_memory()` summarizes older turns into a compact system message:

```text
Conversation summary so far:
...
```

The summary keeps important facts such as:

- user name
- user preferences
- movie facts already found
- goals and unresolved requests

The implementation keeps whole conversation turns together so OpenAI tool-call messages do not get separated from their matching tool responses.

## Available Tools

### `get_movie_info`

Fetches a movie from OMDb.

Inputs:

- `title`
- optional `year`

### `get_list_of_movies_by_genre`

Searches `data/movies.csv` by genre and returns the top `k` matches.

Inputs:

- `genre`
- optional `k`

### `get_list_of_genres`

Returns all available genres from the local CSV dataset.

Inputs:

- none

### `get_newest_movie`

Compares two movie objects by their `Year` field.

Inputs:

- `movie1`
- `movie2`

## Common Issues

### OpenAI returns 401

Check that `.env` contains a valid OpenAI API key:

```env
OPENAI_API_KEY="sk-..."
```

This project reads `.env` directly with `dotenv_values(...)`, so it should ignore machine-level environment variables with the same name.

### OMDb returns an error

Check that:

- `OMDB_API_KEY` is present in `.env`
- the key is active
- the request uses `apikey`, not `token`
- the movie title/year are valid

### Tool-call 400 error

OpenAI requires every assistant message with `tool_calls` to be followed by matching `role: "tool"` messages for each `tool_call_id`.

The agent handles this in `chat_agent(...)`. If you change summary memory or message slicing, make sure you never keep a tool result while removing the assistant tool-call message it responds to.

### CSV file not found

`tools.py` loads the CSV from:

```text
data/movies.csv
```

Download the Kaggle dataset, rename the CSV file to `movies.csv`, and place it inside the `data` folder.

## Development Notes

Run a syntax check:

```bash
python3 -m py_compile agent.py tools.py
```

The live agent is not ideal for automated tests yet because it calls external APIs and then waits for terminal input.
test change 2026-09-28T09:55:20Z - trivial edit to create a fresh diff against testing-target for another guard test
another update to prove re-lock on synchronize 2026-09-28T10:36:58Z
