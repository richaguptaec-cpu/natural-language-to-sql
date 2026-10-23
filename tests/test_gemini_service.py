
import pytest

from services.gemini_service import (
    SQLGenerationError,
    _parse_model_response,
)


def test_parse_valid_sql_response():
    response = """
    {
        "sql": "SELECT name FROM customers",
        "explanation": "Returns customer names."
    }
    """

    result = _parse_model_response(response)

    assert result["sql"] == "SELECT name FROM customers"
    assert result["explanation"] == "Returns customer names."


def test_parse_unsupported_question():
    response = """
    {
        "sql": "",
        "explanation": "The schema does not contain employee data."
    }
    """

    result = _parse_model_response(response)

    assert result["sql"] == ""
    assert "employee data" in result["explanation"]


def test_reject_empty_response():
    with pytest.raises(SQLGenerationError, match="empty response"):
        _parse_model_response("")


def test_reject_invalid_json():
    with pytest.raises(SQLGenerationError, match="invalid JSON"):
        _parse_model_response("This is not JSON")


def test_reject_json_array():
    with pytest.raises(SQLGenerationError, match="JSON object"):
        _parse_model_response("[]")


def test_reject_missing_sql_field():
    response = '{"explanation": "A query explanation."}'

    with pytest.raises(SQLGenerationError, match="'sql'"):
        _parse_model_response(response)


def test_reject_non_string_sql():
    response = """
    {
        "sql": 123,
        "explanation": "A query explanation."
    }
    """

    with pytest.raises(SQLGenerationError, match="'sql'"):
        _parse_model_response(response)


def test_reject_missing_explanation():
    response = '{"sql": "SELECT name FROM customers"}'

    with pytest.raises(SQLGenerationError, match="explanation"):
        _parse_model_response(response)


def test_reject_blank_explanation():
    response = """
    {
        "sql": "SELECT name FROM customers",
        "explanation": "   "
    }
    """

    with pytest.raises(SQLGenerationError, match="explanation"):
        _parse_model_response(response)


def test_trim_whitespace_from_sql():
    response = """
    {
        "sql": "  SELECT name FROM customers  ",
        "explanation": "Returns customer names."
    }
    """

    result = _parse_model_response(response)

    assert result["sql"] == "SELECT name FROM customers"
