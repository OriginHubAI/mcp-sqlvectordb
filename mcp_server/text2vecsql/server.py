"""Text to Vector SQL."""

from dataclasses import dataclass
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
    def handle_response(cls, response: requests.Response) -> "TextToVecSQLResponse":
        """Handle a response from the Text to Vector SQL server."""
        assert response.status_code == 200, (
            f"Error: {response.json()['error_message'] if 'error_message' in response.json() else str(response.json())}"
        )

        # 处理新的聊天完成 API 响应格式
        response_data = response.json()
        if "choices" in response_data and response_data["choices"]:
            # 从聊天完成 API 响应中提取 assistant 回复
            results = response_data["choices"][0]["message"]["content"]
        else:
            # 兼容旧格式
            results = response_data["result"]

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
        return cls(
            results={"handle_step": handle_step, "sql": sql.strip()},
            error_message=None,
            error_code=None,
        )


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
        # 使用新的聊天完成 API 格式
        response = requests.post(
            "https://cloud.infini-ai.com/AIStudio/inference/api/if-dce5zpkpwhejio5f/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "/mnt/DataFlow/ydw/model/UniVectorSQL-7B-LoRA-Step800",
                "messages": [
                    {
                        "role": "system",
                        "content": request.prompt,  # 完整的系统提示词（包含所有 schema 和规则）
                    },
                    {
                        "role": "user",
                        "content": request.natural_language_question,  # 用户的自然语言问题
                    },
                ],
                "max_tokens": 2048,
                "temperature": 0.05,  # SQL 生成任务用较低的温度保证准确性
                "top_p": 0.95,
            },
        )
        return TextToVecSQLResponse.handle_response(response)
    except Exception as e:
        # print("[log] error: ", str(e))
        return TextToVecSQLResponse(
            results={},
            error_message=str(e),
            error_code=response.status_code if "response" in locals() else 500,
        )


def get_vector_query(natural_language_question: str, table_schema: str) -> str:
    """Get a vector query from a natural language question and table schema.

    IMPORTANT: Before calling this tool, you MUST translate the natural_language_question to English if it is not already in English. Find the column names that must be returned in natural_1anguage_question, and you also need to add prompts to inform the model of these column names that must be returned.
    This tool requires English input for optimal performance.

    Use this tool for natural language questions that require a vector query.
    You can use this tool to generate a vector query for a natural language question,
    and then execute the query on the database. And return the results to the user.

    Suitable for:
    - Questions that require a vector query
    - Questions that require a standard SQL query

    Best practices:
    - ALWAYS translate the question to English before calling this tool
    - Use the vector query tool for natural language questions that require a vector query
    - Use the standard SQL query tool for natural language questions that require a standard SQL query

    Use this tool when you need to generate a vector query for a natural language question. And then execute the query on the database.
    Example:
    - Can you unveil the crown jewel of our vegetarian delights, the one that has soared to the top of the sales charts from the elite circle of our most cherished categories this year?
    """
    prompt = TEXT_TO_MYSCALE_VEC_SQL_PROMPT.format(
        TableSchema=table_schema,
        NaturalLanguageQuestion=natural_language_question,
        embedding_model="intfloat/E5-Mistral-7B-Instruct",
    )
    config = get_text_to_vec_sql_config()
    response = do_request(
        config.url,
        config.api_key,
        TextToVecSQLRequest(
            table_schema=table_schema,
            natural_language_question=natural_language_question,
            prompt=prompt,
        ),
    )

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
