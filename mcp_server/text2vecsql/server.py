"""Text to Vector SQL."""

from dataclasses import dataclass
from inspect import FrameInfo
import logging
import requests
import json
from typing import Optional

from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.prompts import Prompt

from ..config import get_text_to_vec_sql_config
from .prompts import TEXT_TO_MYSCALE_VEC_SQL_PROMPT, TEXT2VEC_SQL_PROMPT

logger = logging.getLogger("mcp-text-to-vec-sql")


@dataclass
class TextToVecSQLResponse:
    """Text to Vector SQL response."""
    results: json
    error_message: Optional[str] = None
    error_code: Optional[int] = None

    @classmethod
    def handle_response(cls, response: requests.Response) -> 'TextToVecSQLResponse':
        """Handle a response from the Text to Vector SQL server."""
        assert response.status_code == 200, f"Error: {response.json()['error_message']}"
        results = response.json()["result"]
        handle_step = ""
        sql = ""
        next_is_sql = False
        for result in results.split("\n"):
            if result.startswith("```sql"):
                next_is_sql = True
                continue
            elif result.startswith("```"):
                next_is_sql = False
            elif next_is_sql:
                sql += result + "\n"
            else:
                handle_step += result + "\n"
        return cls(results={"handle_step": handle_step, "sql": sql.strip()}, error_message=None, error_code=None)

@dataclass
class TextToVecSQLRequest:
    """Text to Vector SQL request."""
    table_schema: str
    natural_language_question: str
    prompt: str

@dataclass
class TextToVecSQLConfig:
    """Text to Vector SQL config."""
    url: str
    api_key: str

def do_request(url: str, api_key: str, request: TextToVecSQLRequest) -> TextToVecSQLResponse:
    """Do a request to the Text to Vector SQL server."""
    try:
        response = requests.post(url, json={"text_input": request.prompt}, headers={"Authorization": f"Bearer {api_key}"})
        return TextToVecSQLResponse.handle_response(response)
    except Exception as e:
        return TextToVecSQLResponse(sql="", error_message=str(e), error_code=response.status_code)

def get_vector_query(natural_language_question: str, table_schema: str) -> str:
    """Get a vector query from a natural language question and table schema.
    
    Use this tool for natural language questions that require a vector query.

    Suitable for:
    - Questions that require a vector query
    - Questions that require a standard SQL query

    Best practices:
    - Use the vector query tool for natural language questions that require a vector query
    - Use the standard SQL query tool for natural language questions that require a standard SQL query

    Use this tool when you need to generate a vector query for a natural language question.
    Example:
    - Can you unveil the crown jewel of our vegetarian delights, the one that has soared to the top of the sales charts from the elite circle of our most cherished categories this year?
    """
    prompt = TEXT_TO_MYSCALE_VEC_SQL_PROMPT.format(TableSchema=table_schema, NaturalLanguageQuestion=natural_language_question, embedding_model='intfloat/E5-Mistral-7B-Instruct')
    config = get_text_to_vec_sql_config()
    response = do_request(
        config.url,
        config.api_key,
        TextToVecSQLRequest(table_schema=table_schema, natural_language_question=natural_language_question, prompt=prompt))
    
    # Return formatted string instead of dict for MCP compatibility
    if response.error_message:
        return f"Error: {response.error_message}"
    
    result = response.results
    return f"{result['handle_step']}\n\n```sql\n{result['sql']}\n```"

def text_to_vec_sql_initial_prompt() -> str:
    """Text to Vector SQL initial prompt."""
    return TEXT2VEC_SQL_PROMPT

def register_tools(mcp: FastMCP):
    """Register Text to Vector SQL tools to MCP instance."""
    mcp.add_tool(Tool.from_function(get_vector_query))
    text_to_vec_sql_prompt = Prompt.from_function(
        text_to_vec_sql_initial_prompt,
        name="text_to_vec_sql_initial_prompt",
        description="This prompt helps users understand how to interact with Text to Vector SQL and perform operations.",
    )
    mcp.add_prompt(text_to_vec_sql_prompt)
    logger.info("Text to Vector SQL tools and prompts registered")