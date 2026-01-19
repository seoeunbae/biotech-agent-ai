import sys
from pathlib import Path


import typer
import json
from dotenv import load_dotenv
from eliot import start_action, log_call
from pycomfort.logging import to_nice_file, to_nice_stdout

from just_agents import llm_options
from just_agents.llm_options import LLMOptions
from just_agents.base_agent import BaseAgent
from opengenes_mcp.server import OpenGenesMCP

app = typer.Typer()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEST_DIR = PROJECT_ROOT / "test"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create logs directory
LOGS_DIR.mkdir(parents=True, exist_ok=True)


answers_model = {
    "model": "gemini/gemini-2.5-flash-preview-05-20",
    "temperature": 0.0
}

@log_call()
def run_query(prompt_file: Path, query: str, options: LLMOptions = answers_model, tell_sql: bool = False):
    load_dotenv(override=True)

    # Get prompt content from Hugging Face instead of local file
    from opengenes_mcp.server import get_prompt_content
    system_prompt = get_prompt_content().strip()

    if tell_sql:
        system_prompt += "in your response, include the SQL query that you used to answer the question."

    # Initialize OpenGenes MCP server
    opengenes_server = OpenGenesMCP()
    
    agent = BaseAgent(
        llm_options=options,
        tools=[opengenes_server.db_query, opengenes_server.get_schema_info, opengenes_server.get_example_queries],
        system_prompt=system_prompt
    )

    with start_action(action_type="run_query", query=query) as action:
        action.log(f"question send to the agent: {query}")
        result = agent.query(query)
        action.log(f"LLM AGENT ANSWER: {result}")
        return result

@app.command()
def test_opengenes():
    query_file = TEST_DIR / "test_opengenes.txt"
    
    with query_file.open("r", encoding="utf-8") as f:
        queries = f.readlines()
    
    to_nice_stdout()
    to_nice_file(LOGS_DIR / "test_opengenes_human.json", LOGS_DIR / "test_opengenes_human.log")

    # Collect question-answer pairs
    qa_pairs = []
    
    for query in queries:
        query = query.strip()
        if query:
            answer = run_query(None, query, tell_sql=True)
            qa_pairs.append({
                "question": query,
                "answer": answer
            })
    
    # Save question-answer pairs to JSON file
    qa_json_path = LOGS_DIR / "test_opengenes_qa.json"
    with qa_json_path.open("w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    
    print(f"Question-answer pairs saved to: {qa_json_path}")

if __name__ == "__main__":
    app()