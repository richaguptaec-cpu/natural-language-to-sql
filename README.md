# Natural Language to SQL

Convert plain-English questions into SQL queries using Google Gemini, Python, and SQLite. This project demonstrates how generative AI can simplify database querying while incorporating SQL validation and controlled read-only execution.

## Overview

Natural Language to SQL allows users to ask questions about a sample database without writing SQL manually. The application generates SQL using the database schema, validates the generated query, and optionally executes valid queries against a local SQLite database.

**Key capabilities**
- Natural-language-to-SQL generation using Google Gemini.
- Automatic database schema discovery, including columns and foreign-key relationships.
- SQL parsing and validation using SQLGlot.
- Read-only SQLite query execution with restricted operations.
- Query execution timeout and configurable result-row limits.
- Query history within the current Streamlit session.
- SQL and CSV downloads.
- Automated unit tests using Pytest.

## Technology Stack

- **Language:** Python
- **AI model:** Google Gemini (`gemini-2.5-flash` by default)
- **Frontend:** Streamlit
- **Database:** SQLite
- **SQL parsing:** SQLGlot
- **Testing:** Pytest
- **Configuration:** python-dotenv

## Architecture

```text
User's Natural Language Question
                |
                v
       Streamlit Application
                |
                v
       Gemini SQL Generator
                |
                v
       Response Validation
                |
                v
         SQL Validator
                |
                v
       Validated SQL Query
                |
                v
    Optional Read-Only Execution
                |
                v
        SQLite Sample DB
                |
                v
     Results, History & Downloads
```

## Project Structure

```text
natural-language-to-sql/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── database/
│   └── init_db.py
├── services/
│   ├── __init__.py
│   ├── gemini_service.py
│   ├── schema_service.py
│   ├── sql_validator.py
│   └── query_service.py
└── tests/
    ├── test_gemini_service.py
    ├── test_sql_validator.py
    └── test_query_service.py
```

The `database/sample.db` file is generated locally and should not be committed to Git.

## Getting Started

### 1. Prerequisites

- Python installed.
- A Google Gemini API key.
- Git.
- A terminal or VS Code.

### 2. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd natural-language-to-sql
```

Replace the placeholder with your actual GitHub repository URL.

### 3. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python executable directly instead.

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure the Gemini API key

Copy `.env.example` to `.env` and add your API key.

```dotenv
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 6. Initialize the sample database

```powershell
python database/init_db.py
```

This creates the local SQLite database and sample tables for customers, products, and orders.

### 7. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal by Streamlit.

## Example Questions

Try asking:

- Show customers from Sydney.
- List all products and their prices.
- Calculate total spending for each customer.
- Show the number of orders for each customer.
- Show employee salaries.

The last question should be treated as unsupported because the sample database does not contain employee or salary data. The application should not invent missing tables or columns.

## Application Screenshots

### 1. Home Page

The main interface for entering natural-language questions and choosing whether to execute validated SQL.

<img width="741" height="517" alt="image" src="https://github.com/user-attachments/assets/9a28f088-bc6c-4e81-b398-0fa7107788f4" />


### 2. Database Schema Discovery

Displays the available SQLite tables, columns, and relationships used to guide SQL generation.

<img width="911" height="257" alt="image" src="https://github.com/user-attachments/assets/71070f4b-4df3-46f8-a91d-7993c0a0e76d" />

### 3. AI-Powered SQL Generation

Converts a natural-language question into a SQLite query and provides an explanation.

<img width="1043" height="626" alt="image" src="https://github.com/user-attachments/assets/a4b9b362-db87-4b8f-ae1b-5a0e6906640a" />

### 4. SQL Validation

Validates generated SQL against the supported query policy and database schema before execution.

<img width="680" height="573" alt="image" src="https://github.com/user-attachments/assets/49d7331a-73da-49f8-a252-503eadca4846" />

### 5. Read-Only Query Execution

Displays the actual query results, with row limits and a CSV export option.

<img width="987" height="485" alt="image" src="https://github.com/user-attachments/assets/7fdb2844-bb74-4d48-b998-963369c1590b" />

### 6. Query History

Allows users to review previously generated queries, explanations, validation status, and execution results during the current session.

<img width="965" height="515" alt="image" src="https://github.com/user-attachments/assets/2153a234-297b-4ef1-99f9-bcde5b548438" />

### 7. SQL and CSV Downloads

Provides downloadable SQL queries and CSV files containing query results.

<img width="353" height="137" alt="image" src="https://github.com/user-attachments/assets/855d4050-8c01-466a-a2c9-176533f8be0c" />


### 8. Automated Test Coverage

Pytest results demonstrating automated checks for SQL generation response parsing, SQL validation, and read-only execution.

<img width="860" height="443" alt="image" src="https://github.com/user-attachments/assets/4f01eff0-77bc-4bfe-b6e8-fc7f7298f261" />

## SQL Validation and Safety

AI-generated SQL is untrusted input. The application validates SQL before it can be executed.

The current implementation includes:

- Single-statement validation.
- SELECT-only query policy.
- Table and column checks against the actual database schema.
- Rejection of unknown tables, columns, and aliases.
- Rejection of unsupported query constructs.
- Read-only database connection for query execution.
- SQLite authorizer restrictions on writes and administrative operations.
- Query execution timeout and result-row limits.

**Current limitations:** The initial SQL validator intentionally rejects CTEs, subqueries, and UNION queries. Some otherwise valid SQL may therefore be rejected. SQL validation and read-only execution provide defence in depth, but they should not be treated as a complete security boundary for untrusted production workloads.

## Running the Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

The tests cover SQL generation response parsing, valid queries, invalid SQL, schema validation, aggregation, read-only execution, and result limits.

The test suite should run without making live Gemini API calls for tests that exercise response parsing and SQL validation. Integration tests that call the real Gemini API, if added, may require credentials and network access.

## Current Limitations

- Uses a local sample SQLite database rather than a production database.
- Query history is stored in Streamlit session state and is not persistent.
- SQL generation depends on Gemini API availability, credentials, and quota.
- The supported SQL subset is intentionally limited.
- Generated SQL must still be reviewed and validated; AI output is not guaranteed to be correct.

## Future Enhancements

- SQL quality scoring and more detailed validation feedback.
- Persistent query history.
- Support for additional SQL constructs with expanded security tests.
- More sample datasets and database schemas.
- Improved handling of ambiguous questions and user clarification.
- Expanded automated and integration test coverage.
- Docker-based deployment and CI automation.

## Learning Outcomes

This project demonstrates practical experience with:

- Generative AI integration.
- Prompt engineering and structured responses.
- Python service-layer design.
- SQL parsing and schema-aware validation.
- Secure database access patterns.
- Automated testing with Pytest.
- Streamlit application development.
- Error handling and responsible use of AI-generated code.

---

**Disclaimer:** This is a learning and portfolio project. Review and validate generated SQL before using similar techniques with sensitive or production data.

**Author:** Richa Gupta  
**GitHub:** [richaguptaec-cpu](https://github.com/richaguptaec-cpu)
