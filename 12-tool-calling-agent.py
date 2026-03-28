# AI-generated PR — review this code
# Description: "Added tool-calling agent loop with memory for multi-step task execution"

import json
from typing import List, Dict, Any, Callable
from openai import OpenAI
from datetime import datetime

client = OpenAI()

MODEL = "gpt-4o"

tools_registry: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: Dict, fn: Callable):
    tools_registry[name] = {
        "definition": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        },
        "fn": fn,
    }


def get_tool_definitions() -> List[Dict]:
    return [t["definition"] for t in tools_registry.values()]


def execute_tool(name: str, arguments: Dict) -> str:
    tool = tools_registry.get(name)
    if not tool:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = tool["fn"](**arguments)
        return json.dumps(result) if not isinstance(result, str) else result
    except Exception as e:
        return json.dumps({"error": str(e)})


class Agent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.tool_call_count = 0

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=get_tool_definitions(),
                tool_choice="auto",
            )

            message = response.choices[0].message
            self.messages.append(message)

            if message.tool_calls:
                for tool_call in message.tool_calls:
                    self.tool_call_count += 1
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)

                    print(f"[Agent] Calling tool: {fn_name}({fn_args})")
                    result = execute_tool(fn_name, fn_args)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                return message.content

    def get_conversation_history(self) -> List[Dict]:
        return self.messages

    def clear_history(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.tool_call_count = 0


# Register example tools
register_tool(
    name="search_database",
    description="Search the company database for records",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "table": {"type": "string", "description": "Table to search"},
        },
        "required": ["query", "table"],
    },
    fn=lambda query, table: {"results": [], "query": query, "table": table},
)

register_tool(
    name="send_email",
    description="Send an email to a recipient",
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to", "subject", "body"],
    },
    fn=lambda to, subject, body: {"status": "sent", "to": to},
)

register_tool(
    name="create_report",
    description="Generate a report from data",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "data": {"type": "object"},
            "format": {"type": "string", "enum": ["pdf", "csv", "json"]},
        },
        "required": ["title", "data"],
    },
    fn=lambda title, data, format="json": {"report_id": "rpt_001", "title": title},
)


if __name__ == "__main__":
    agent = Agent(
        system_prompt="You are a helpful assistant that can search databases, send emails, and create reports."
    )

    result = agent.run("Find all overdue invoices and email a summary to finance@company.com")
    print(result)
