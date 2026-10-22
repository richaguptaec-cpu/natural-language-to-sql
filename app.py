
import streamlit as st

from services.gemini_service import (
    SQLGenerationError,
    generate_sql,
)


st.set_page_config(
    page_title="Natural Language to SQL",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 AI-Powered Natural Language to SQL")
st.caption(
    "Convert plain-English questions into SQL using Gemini AI."
)

st.info(
    "This version generates SQL for review only. "
    "It does not execute queries against a database."
)

question = st.text_area(
    "What data would you like to retrieve?",
    placeholder=(
        "Example: Show all customers from Sydney "
        "who registered in 2025."
    ),
    height=120,
    max_chars=2000,
)

generate_button = st.button(
    "Generate SQL",
    type="primary",
)

if generate_button:
    if not question or not question.strip():
        st.warning("Please enter a question first.")

    else:
        try:
            with st.spinner("Generating SQL with Gemini..."):
                result = generate_sql(question)

            st.subheader("Generated SQL")

            if result["sql"]:
                st.code(result["sql"], language="sql")
                st.download_button(
                    label="Download SQL",
                    data=result["sql"],
                    file_name="generated_query.sql",
                    mime="text/plain",
                )
            else:
                st.warning(
                    "No SQL query was generated. "
                    "Review the clarification below."
                )

            st.subheader("Explanation")
            st.write(
                result["explanation"]
                or "No explanation was provided."
            )

            st.warning(
                "Review and validate generated SQL before "
                "using it against any database."
            )

        except ValueError as exc:
            st.warning(str(exc))

        except SQLGenerationError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "Something went wrong. Please try again."
            )

st.divider()

st.caption(
    "Python | Streamlit | Google Gemini | SQL | Pytest"
)
