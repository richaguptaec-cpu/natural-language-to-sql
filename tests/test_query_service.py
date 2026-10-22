
import pytest

from database.init_db import initialize_database
from services.query_service import execute_read_only_query


@pytest.fixture(autouse=True)
def setup_database():
    # Creates the sample database if it doesn't already exist.
    initialize_database()


def test_execute_valid_select():
    result = execute_read_only_query(
        "SELECT name FROM customers WHERE city = 'Sydney'"
    )

    assert result["columns"] == ["name"]
    assert len(result["rows"]) == 2
    assert result["truncated"] is False


def test_execute_join_and_aggregation():
    sql = """
        SELECT c.name,
               SUM(o.quantity * p.price) AS total_spent
        FROM customers AS c
        JOIN orders AS o ON c.customer_id = o.customer_id
        JOIN products AS p ON o.product_id = p.product_id
        GROUP BY c.customer_id, c.name
        ORDER BY total_spent DESC
    """

    result = execute_read_only_query(sql)

    assert result["row_count"] == 3
    assert result["rows"][0][0] == "Alice"
    assert result["rows"][0][1] == pytest.approx(2200.0)


def test_result_limit():
    result = execute_read_only_query(
        "SELECT name FROM customers",
        max_rows=1,
    )

    assert result["row_count"] == 1
    assert result["truncated"] is True


def test_reject_delete_before_execution():
    with pytest.raises(ValueError, match="SQL validation failed"):
        execute_read_only_query("DELETE FROM customers")


def test_reject_unknown_table_before_execution():
    with pytest.raises(ValueError, match="SQL validation failed"):
        execute_read_only_query("SELECT * FROM employees")
