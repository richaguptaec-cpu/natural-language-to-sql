import streamlit as st

st.set_page_config(
    page_title="Natural Language to SQL",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Natural Language to SQL Generator")

st.markdown(
    """
    Convert plain-English business questions into SQL queries.

    Enter your question below. The AI integration will be
    added in the next milestone.
    """
)

question = st.text_area(
    "Describe the data you want to retrieve",
    placeholder=(
        "Example: Show all customers from Sydney "
        "who registered in 2025."
    ),
    height=120,
)

if st.button("Generate SQL", type="primary"):
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        st.info(
            "Your question has been captured. "
            "Gemini integration is coming in Step 2."
        )
        st.write("**Your question:**")
        st.write(question.strip())

st.divider()

st.caption(
    "Portfolio project | Python | Streamlit | Gemini | SQLite"
)