
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"
DB_PATH = DATABASE_DIR / "sample.db"


def initialize_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                email TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                price REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id),
                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
            );

            INSERT OR IGNORE INTO customers
                (customer_id, name, city, email)
            VALUES
                (1, 'Alice', 'Sydney', 'alice@example.com'),
                (2, 'Bob', 'Melbourne', 'bob@example.com'),
                (3, 'Charlie', 'Sydney', 'charlie@example.com');

            INSERT OR IGNORE INTO products
                (product_id, product_name, price)
            VALUES
                (1, 'Laptop', 1500.00),
                (2, 'Monitor', 350.00),
                (3, 'Keyboard', 100.00);

            INSERT OR IGNORE INTO orders
                (order_id, customer_id, product_id, quantity, order_date)
            VALUES
                (101, 1, 1, 1, '2025-01-15'),
                (102, 1, 2, 2, '2025-02-10'),
                (103, 2, 3, 1, '2025-03-05'),
                (104, 3, 2, 1, '2025-04-20');
        """)

    print(f"Database initialized successfully: {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
