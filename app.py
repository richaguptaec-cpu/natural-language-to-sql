
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

st.title("🧠 AI-Powered Natural Language to SQL")
st.caption(
    "Generate, validate, and optionally execute SQL against a sample SQLite database."
)

st.info(
    "Execution is optional. Queries must pass validation first, and "
    "SQLite is opened in read-only mode."
)

try:
    schema = get_database_schema()
except Exception as exc:
    schema = ""
    st.error(f"Could not load the database schema: {exc}")

with st.expander("View connected database schema"):
    if schema:
        st.code(schema, language="sql")

question = st.text_area(
    "What data would you like to retrieve?",
    placeholder="Example: Calculate the total amount spent by each customer.",
    height=120,
    max_chars=2000,
)

execute_after_validation = st.checkbox(
    "Execute validated SQL against the sample database",
    value=False,
    help="Only read-only queries that pass SQL validation will be executed.",
)

if st.button("Generate and Validate SQL", type="primary"):
    if not question or not question.strip():
        st.warning("Please enter a question first.")
    elif not schema:
        st.error("The database schema could not be loaded.")
    else:
        try:
            with st.spinner("Generating SQL with Gemini..."):
                result = generate_sql(question, schema)

            st.subheader("Explanation")
            st.write(result["explanation"] or "No explanation provided.")

            if not result["sql"]:
                st.warning("Gemini did not generate a SQL query.")
            else:
                validation = validate_sql(result["sql"])

                if not validation["valid"]:
                    st.error("SQL validation failed. The query was rejected.")
                    for error in validation["errors"]:
                        st.write(f"- {error}")

                    with st.expander("View rejected SQL"):
                        st.code(result["sql"], language="sql")

                else:
                    validated_sql = validation["sql"]
                    st.success("SQL validation passed.")
                    st.subheader("Validated SQL")
                    st.code(validated_sql, language="sql")

                    st.download_button(
                        "Download validated SQL",
                        data=validated_sql,
                        file_name="validated_query.sql",
                        mime="text/plain",
                    )

                    if execute_after_validation:
                        try:
                            with st.spinner("Executing read-only query..."):
                                query_result = execute_read_only_query(
                                    validated_sql
                                )

                            st.subheader("Query results")
                            st.caption(
                                f"Returned {query_result['row_count']} row(s)."
                            )

                            if query_result["columns"]:
                                result_records = [
                                    dict(zip(query_result["columns"], row))
                                    for row in query_result["rows"]
                                ]
                                st.dataframe(
                                    result_records,
                                    use_container_width=True,
                                )

                                csv_buffer = io.StringIO()
                                writer = csv.writer(csv_buffer)
                                writer.writerow(query_result["columns"])
                                writer.writerows(query_result["rows"])

                                st.download_button(
                                    "Download results as CSV",
                                    data=csv_buffer.getvalue(),
                                    file_name="query_results.csv",
                                    mime="text/csv",
                                )
                            else:
                                st.info("The query returned no tabular results.")

                            if query_result["truncated"]:
                                st.warning(
                                    "Results were limited to 500 rows. "
                                    "Refine the query to retrieve a smaller result set."
                                )

                        except TimeoutError as exc:
                            st.error(str(exc))
                        except (ValueError, RuntimeError, FileNotFoundError) as exc:
                            st.error(f"Query execution failed: {exc}")
                    else:
                        st.info(
                            "Execution is disabled. Select the checkbox above "
                            "to run validated SQL against the sample database."
                        )

        except ValueError as exc:
            st.warning(str(exc))
        except SQLGenerationError as exc:
            st.error(str(exc))

st.divider()
st.caption(
    "Python | Streamlit | Google Gemini | SQLite | SQLGlot | Pytest"
)
