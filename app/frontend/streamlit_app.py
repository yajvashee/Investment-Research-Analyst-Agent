"""Presentation-only Streamlit frontend for the existing FastAPI backend."""
from __future__ import annotations

import streamlit as st

try:
    from app.frontend.client import submit_research
except ModuleNotFoundError:
    from client import submit_research


st.set_page_config(page_title="Investment Research Analyst", page_icon="chart", layout="wide")
st.title("Investment Research Analyst")
st.write("Ask research questions using historical financial data, current/recent market data, company reports, and an AI research agent.")

mode = st.radio(
    "What would you like to do?",
    ["General research", "Example strategy for my situation"],
    horizontal=True,
)

amount = 0.0
risk = "Not specified"
horizon = "Not specified"
if mode == "Example strategy for my situation":
    st.caption("These details provide context for an educational example; they do not create personalised financial advice.")
    left, right = st.columns(2)
    with left:
        amount = st.number_input("Investment amount (GBP, optional)", min_value=0.0, value=0.0, step=100.0)
        risk = st.selectbox("Risk preference", ["Not specified", "Lower risk", "Balanced", "Higher risk"])
    with right:
        horizon = st.selectbox("Time horizon", ["Not specified", "Short term", "Medium term", "Long term"])
        st.caption("Choose these only when you want an example strategy.")
else:
    st.caption("Use this for company comparisons, financial trends, company risks, or document-based questions.")

placeholder = (
    "Compare Microsoft and Apple as investments."
    if mode == "General research"
    else "I have 1000 GBP to invest. Give me a balanced example strategy using the companies in the dataset."
)
question = st.text_area("Your research question", placeholder=placeholder, height=100)

if st.button("Analyze", type="primary"):
    if not question.strip():
        st.error("Please enter a research question.")
    else:
        payload = {"question": question.strip()}
        if amount > 0:
            payload["investment_amount"] = amount
        if risk != "Not specified":
            payload["risk_preference"] = risk.lower().replace(" risk", "")
        if horizon != "Not specified":
            payload["time_horizon"] = horizon.lower().replace(" term", "")
        try:
            with st.spinner("Researching available data sources..."):
                result = submit_research(payload)
        except RuntimeError as error:
            st.error(str(error))
        else:
            st.subheader("Research Summary")
            st.write(result["answer"])
            if result.get("companies_analyzed"):
                st.subheader("Companies Analyzed")
                st.write(", ".join(result["companies_analyzed"]))
            if result.get("sources"):
                st.subheader("Data Sources")
                for source in result["sources"]:
                    company = source.get("company_name", source.get("ticker", "Company"))
                    document = source.get("document_name", "Document")
                    st.write(f"- {company}: {document} - {source.get('source', 'Source unavailable')}")
            if result.get("tools_used"):
                st.subheader("Tools Used")
                st.write(", ".join(result["tools_used"]))
            if result.get("warnings"):
                st.subheader("Warnings")
                for warning in result["warnings"]:
                    st.warning(warning)

st.divider()
st.caption("This application provides educational investment research and does not constitute personalised financial advice.")
