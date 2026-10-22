
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError


# Load environment variables from the project-root .env file.
load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"


class SQLGenerationError(Exception):
    """Raised when SQL generation fails."""


def generate_sql(question: str) -> dict[str, str]:
    """
    Generate SQL and an explanation from a natural-language question.

    Returns:
        {
            "sql": "...",
            "explanation": "..."
        }

    This function generates SQL only. It does not execute it.
    """
    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_api_key_here":
        raise SQLGenerationError(
            "Gemini API key is missing. Add GEMINI_API_KEY "
            "to your project-root .env file."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip()

    if not model:
        model = DEFAULT_MODEL

    prompt = f"""
You are an assistant that translates natural-language questions
into SQL for a relational database.

The database schema has not been provided yet. Do not invent
table or column names as if they were verified.

Rules:
1. Generate one SQL query that best matches the request.
2. Do not execute the query or modify any database.
3. Prefer read-only SELECT queries.
4. If the request is ambiguous or lacks essential information,
   explain what needs clarification and return an empty SQL string.
5. Return valid JSON only, with exactly these keys:
   "sql": the generated SQL string, or an empty string.
   "explanation": a concise explanation or clarification request.
6. Do not include Markdown code fences around the JSON.

User request:
{question.strip()}
"""

    try:
        with genai.Client(api_key=api_key) as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

        response_text = response.text

        if not response_text or not response_text.strip():
            raise SQLGenerationError(
                "Gemini returned an empty response. Please try again."
            )

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise SQLGenerationError(
                "Gemini returned an invalid response format. "
                "Please try again."
            ) from exc

        if not isinstance(result, dict):
            raise SQLGenerationError(
                "Gemini returned an unexpected response structure."
            )

        sql = result.get("sql")
        explanation = result.get("explanation")

        if not isinstance(sql, str) or not isinstance(
            explanation, str
        ):
            raise SQLGenerationError(
                "Gemini's response is missing the expected fields."
            )

        return {
            "sql": sql.strip(),
            "explanation": explanation.strip(),
        }

    except SQLGenerationError:
        raise
    except APIError as exc:
        # Do not expose credentials or raw provider errors in the UI.
        raise SQLGenerationError(
            "Gemini API request failed. Check your API key, "
            "model availability, API quota, and network connection."
        ) from exc
    except Exception as exc:
        raise SQLGenerationError(
            "An unexpected error occurred while generating SQL."
        ) from exc
    