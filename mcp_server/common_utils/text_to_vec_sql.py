"""Text to Vector SQL."""

import logging

from ..config import get_text_to_vec_sql_config

logger = logging.getLogger("mcp-text-to-vec-sql")


class TextToVecSQL:
    """Text to Vector SQL client."""

    def __init__(self):
        """Initialize the Text to Vector SQL client."""
        self.config = get_text_to_vec_sql_config()

    def generate_vec_sql_from_text(self, text: str, sql_engine: str) -> str:
        """Generate a vector SQL from text."""
        logging.debug(f"Generating vector SQL from text: {text} for SQL engine: {sql_engine}")
        pass
    
_TEXT_TO_VEC_SQL_INSTANCE = None

def get_text_to_vec_sql_instance() -> TextToVecSQL:
    """Get the singleton instance of TextToVecSQL."""
    global _TEXT_TO_VEC_SQL_INSTANCE
    if _TEXT_TO_VEC_SQL_INSTANCE is None:
        _TEXT_TO_VEC_SQL_INSTANCE = TextToVecSQL()
    return _TEXT_TO_VEC_SQL_INSTANCE