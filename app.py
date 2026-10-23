
import csv
import io

import streamlit as st

from services.gemini_service import SQLGenerationError, generate_sql
from services.schema_service import get_database_schema
from services.sql_validator import validate_sql
from services.query_service import execute_read_only_query


st.set_page_config(
    page_title="Natural Language to SQL",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Natural Language to SQL")
st.caption(
    "Convert natural-language questions into validated SQLite queries "
    "using Google Gemini."
)

# Initialise session state.
if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "next_query_id" not in st.session_state:
    st.session_state.next_query_id = 1


def create_csv(columns, rows):
    """Convert query results into downloadable CSV content."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    return output.getvalue()


# Display the actual database schema.
try:
    schema = get_database_schema()

    with st.expander("View database schema"):
        st.code(schema, language="sql")

except (FileNotFoundError, OSError, RuntimeError) as exc:
    st.error(f"Could not load the database schema: {exc}")
    st.stop()


st.subheader("Ask a question")

question = st.text_area(
    "Enter your question in plain English",
    placeholder=(
        "Example: Show customers from Sydney\n"
        "Example: Calculate total spending for each customer"
    ),
    height=100,
)

execute_query = st.checkbox(
    "Execute validated SQL against the sample database",
    value=False,
    help="Only validated queries are eligible for execution.",
)

if st.button("Generate SQL", type="primary"):
    if not question.strip():
        st.warning("Please enter a question first.")

    else:
        query_record = {
            "id": st.session_state.next_query_id,
            "question": question.strip(),
            "sql": "",
            "explanation": "",
            "validation": None,
            "execution": None,
            "error": None,
        }

        st.session_state.next_query_id += 1

        try:
            with st.spinner("Generating SQL with Gemini..."):
                generated = generate_sql(
                    question=question.strip(),
                    schema=schema,
                )

            sql = generated.get("sql", "").strip()
            explanation = generated.get("explanation", "")

            query_record["sql"] = sql
            query_record["explanation"] = explanation

            if not sql:
                query_record["error"] = (
                    "No SQL query was generated. "
                    "Try asking a more specific question."
                )
            else:
                validation = validate_sql(sql)
                query_record["validation"] = validation

                if validation["valid"]:
                    query_record["sql"] = validation.get("sql", sql)

                    if execute_query:
                        with st.spinner("Executing read-only query..."):
                            query_record["execution"] = (
                                execute_read_only_query(
                                    query_record["sql"]
                                )
                            )
                else:
                    query_record["error"] = (
                        "SQL validation failed: "
                        + "; ".join(validation["errors"])
                    )

        except SQLGenerationError as exc:
            query_record["error"] = f"SQL generation failed: {exc}"

        except (TimeoutError, ValueError, RuntimeError, FileNotFoundError) as exc:
            query_record["error"] = str(exc)

        except Exception:
            # Avoid displaying API credentials or internal tracebacks.
            query_record["error"] = (
                "An unexpected error occurred. "
                "Check the terminal logs and application configuration."
            )

        st.session_state.query_history.append(query_record)


# Show the most recently generated query.
if st.session_state.query_history:
    latest = st.session_state.query_history[-1]

    st.divider()
    st.subheader("Latest query")

    st.markdown("**Question**")
    st.write(latest["question"])

    if latest["sql"]:
        st.markdown("**Generated SQL**")
        st.code(latest["sql"], language="sql")

        st.download_button(
            "Download SQL",
            data=latest["sql"],
            file_name=f"query_{latest['id']}.sql",
            mime="text/sql",
            key=f"download_sql_{latest['id']}",
        )

    if latest["explanation"]:
        st.markdown("**Explanation**")
        st.write(latest["explanation"])

    validation = latest["validation"]

    if validation:
        if validation["valid"]:
            st.success("SQL validation passed.")
        else:
            st.error("SQL validation failed.")
            for error in validation["errors"]:
                st.write(f"- {error}")

    if latest["error"]:
        st.error(latest["error"])

    result = latest["execution"]

    if result is not None:
        st.markdown("**Query results**")

        if result["rows"]:
            st.dataframe(
                [
                    dict(zip(result["columns"], row))
                    for row in result["rows"]
                ],
                use_container_width=True,
            )
        else:
            st.info("The query returned no rows.")

        st.caption(f"Rows displayed: {result['row_count']}")

        if result["truncated"]:
            st.warning(
                "Results were limited. Increase the configured row limit "
                "if you need to retrieve more rows."
            )

        st.download_button(
            "Download results as CSV",
            data=create_csv(result["columns"], result["rows"]),
            file_name=f"query_results_{latest['id']}.csv",
            mime="text/csv",
            key=f"download_csv_{latest['id']}",
        )


# Query history panel.
st.divider()

history = st.session_state.query_history

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Query history ({len(history)})")

with col2:
    if history and st.button("Clear history"):
        st.session_state.query_history = []
        st.rerun()

if not history:
    st.info("Your generated queries will appear here.")
else:
    for record in reversed(history):
        with st.expander(
            f"Query #{record['id']}: {record['question']}"
        ):
            if record["sql"]:
                st.markdown("**SQL**")
                st.code(record["sql"], language="sql")

            if record["explanation"]:
                st.markdown("**Explanation**")
                st.write(record["explanation"])

            validation = record["validation"]

            if validation:
                if validation["valid"]:
                    st.success("Validation passed")
                else:
                    st.error("Validation failed")
                    for error in validation["errors"]:
                        st.write(f"- {error}")

            if record["error"]:
                st.warning(record["error"])

            result = record["execution"]

            if result is not None:
                st.markdown("**Execution results**")

                if result["rows"]:
                    st.dataframe(
                        [
                            dict(zip(result["columns"], row))
                            for row in result["rows"]
                        ],
                        use_container_width=True,
                    )
                else:
                    st.info("No rows returned.")

                st.download_button(
                    "Download this query's results",
                    data=create_csv(result["columns"], result["rows"]),
                    file_name=f"query_results_{record['id']}.csv",
                    mime="text/csv",
                    key=f"history_csv_{record['id']}",
                )