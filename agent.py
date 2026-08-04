import json
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI

from tools import tools, tool_map

config = dotenv_values(Path(__file__).with_name(".env"))
SUMMARY_PREFIX = "Conversation summary so far:\n"

conversation_history = [
    {"role": "system",
     "content": (
         "You are a helpful movie assistant with short-term memory. "
         "Remember facts the user tells you during this conversation, such as their name. "
         "Use tools only for movie information. "
         "Before using a tool, briefly explain what you are going to check and why. "
         "Do not reveal hidden chain-of-thought; only provide a short action summary."
     )}
]

summary_memory = ""


def require_config_value(name):
    value = config.get(name)
    if not value or not value.strip():
        raise Exception(f"You must provide {name} in .env file, see example in .env.example file")
    return value.strip()


def require_positive_int(name):
    value = require_config_value(name)
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise Exception(f"{name} must be a positive integer") from exc
    if parsed_value <= 0:
        raise Exception(f"{name} must be a positive integer")
    return parsed_value


client = OpenAI(api_key=require_config_value("OPENAI_API_KEY"))
max_cycles = require_positive_int("MAX_CYCLES")
max_recent_messages = require_positive_int("MAX_RECENT_MESSAGES")


def print_separator():
    print("\n")
    print(60 * "-")


def chat_agent(user_input):
    print("User prompt: ", user_input)
    conversation_history.append({"role": "user", "content": user_input})

    for _ in range(int(max_cycles)):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            tools=tools
        )

        message = response.choices[0].message
        conversation_history.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            print(message.content)
            return message.content

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_function = tool_map.get(tool_name)

            if tool_function is None:
                tool_output = {"error": f"Unknown tool: {tool_name}"}
            else:
                args = json.loads(tool_call.function.arguments)
                print(f"Reasoning: I will call {tool_name} with {args} to get the needed information.")
                tool_output = tool_function(**args)

            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_output),
            })

    final_text = "I could not finish because too many tool calls were needed."
    conversation_history.append({"role": "assistant", "content": final_text})
    print(final_text)
    return final_text


def maybe_summarize_memory():
    global summary_memory, conversation_history
    system_message = conversation_history[0]
    non_system_messages = [
        message for message in conversation_history[1:]
        if not is_summary_message(message)
    ]

    if len(non_system_messages) <= max_recent_messages:
        return

    turns = split_into_turns(non_system_messages)
    recent_turns = []
    recent_count = 0

    while turns:
        next_turn = turns[-1]
        if recent_turns and recent_count + len(next_turn) > max_recent_messages:
            break
        recent_turns.insert(0, turns.pop())
        recent_count += len(next_turn)

    old_messages = flatten_turns(turns)
    recent_messages = flatten_turns(recent_turns)

    if not old_messages:
        return

    summary_prompt = [
        {
            "role": "system",
            "content": (
                "Summarize the conversation for future context. "
                "Keep user name, preferences, goals, movie facts already found, "
                "and unresolved requests. Be concise."
            )
        },
        {
            "role": "user",
            "content": (
                f"Previous summary:\n{summary_memory}\n\n"
                f"Older messages to summarize:\n{old_messages}"
            )
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=summary_prompt
    )

    summary_memory = response.choices[0].message.content

    conversation_history = [
        system_message,
        {
            "role": "system",
            "content": f"{SUMMARY_PREFIX}{summary_memory}"
        },
        *recent_messages
    ]


def is_summary_message(message):
    return (
            message.get("role") == "system"
            and message.get("content", "").startswith(SUMMARY_PREFIX)
    )


def split_into_turns(messages):
    turns = []
    current_turn = []

    for message in messages:
        if message.get("role") == "user" and current_turn:
            turns.append(current_turn)
            current_turn = [message]
        else:
            current_turn.append(message)

    if current_turn:
        turns.append(current_turn)

    return turns


def flatten_turns(turns):
    return [message for turn in turns for message in turn]


def start_chatting():
    initial_prompts = [
        "my name is Samat, and I love watching movies, remember my name",
        "is there a movie with name 'Mortal Kombat' and release year as 1995?",
        "What is my name?",
        "give me exact release date",
        "Here are two movies I want to compare, 'Moneyball' and 'Mortal Kombat' year 1995, which one is newer?",
        "Find me the list of movies with genre 'custom'",
        "Find me the list of movies with genre 'Adventure'",
        "Find me the list of movies with genre 'Adventure', give me top 1 only",
        "What is my name?",
        "give me exact release date of 'Mortal Kombat'"
    ]

    for prompt in initial_prompts:
        print_separator()
        chat_agent(prompt)
        maybe_summarize_memory()

    user_input = None

    while user_input != "gandalf":
        user_input = input("Your prompt: ")

        if user_input.lower() != "gandalf":
            chat_agent(user_input)
            maybe_summarize_memory()
            print_separator()

    print("Bye Bye!!!")


if __name__ == "__main__":
    start_chatting()
