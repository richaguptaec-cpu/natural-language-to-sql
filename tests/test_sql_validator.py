
import pytest

from services.sql_validator import validate_sql


def test_valid_select():
    result = validate_sql(
        "SELECT name FROM customers WHERE city = 'Sydney'"
    )
    assert result["valid"] is True


def test_valid_join_and_aggregation():
    sql = """
        SELECT c.name,
               SUM(o.quantity * p.price) AS total_spent
        FROM customers AS c
        JOIN orders AS o ON c.customer_id = o.customer_id
        JOIN products AS p ON o.product_id = p.product_id
        GROUP BY c.customer_id, c.name
        ORDER BY total_spent DESC
    """
    assert validate_sql(sql)["valid"] is True


def test_reject_empty_sql():
    assert validate_sql("")["valid"] is False
    assert validate_sql("   ")["valid"] is False


def test_reject_unknown_table():
    result = validate_sql("SELECT * FROM employees")
    assert result["valid"] is False
    assert any("Unknown table" in e for e in result["errors"])


def test_reject_unknown_column():
    result = validate_sql("SELECT salary FROM customers")
    assert result["valid"] is False
    assert any("Unknown column" in e for e in result["errors"])


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers",
        "UPDATE customers SET city = 'Perth'",
        "INSERT INTO customers (name) VALUES ('Eve')",
        "DROP TABLE customers",
        "PRAGMA table_info(customers)",
    ],
)
def test_reject_non_select_statements(sql):
    assert validate_sql(sql)["valid"] is False


def test_reject_multiple_statements():
    result = validate_sql(
        "SELECT name FROM customers; DROP TABLE customers;"
    )
    assert result["valid"] is False


def test_reject_invalid_syntax():
    assert validate_sql("SELECT FROM WHERE")["valid"] is False


def test_reject_ambiguous_column():
    result = validate_sql("""
        SELECT customer_id
        FROM customers
        JOIN orders ON customers.customer_id = orders.customer_id
    """)
    assert result["valid"] is False
    assert any("Ambiguous column" in e for e in result["errors"])


def test_reject_unknown_alias():
    result = validate_sql("SELECT x.name FROM customers AS c")
    assert result["valid"] is False
    assert any("Unknown table alias" in e for e in result["errors"])


def test_reject_union_in_initial_policy():
    result = validate_sql(
        "SELECT name FROM customers UNION SELECT product_name FROM products"
    )
    assert result["valid"] is False


def test_reject_cte():
    result = validate_sql("""
        WITH sydney_customers AS (
            SELECT * FROM customers WHERE city = 'Sydney'
        )
        SELECT * FROM sydney_customers
    """)
    assert result["valid"] is False


def test_reject_subquery():
    result = validate_sql(
        "SELECT * FROM (SELECT name FROM customers) AS c"
    )
    assert result["valid"] is False


def test_reject_blocked_function():
    result = validate_sql("SELECT load_extension('example')")
    assert result["valid"] is False
