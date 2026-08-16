"""Presentation-only Streamlit frontend for the existing FastAPI backend."""
from __future__ import annotations
import streamlit as st

# Streamlit runs this file as a script, while health checks import it as a
# package. Supporting both keeps the UI command and the project tests simple.
try:
    from app.frontend.client import submit_research
except ModuleNotFoundError:
    from client import submit_research

st.set_page_config(page_title="Investment Research Analyst", page_icon="📈", layout="wide")
st.title("Investment Research Analyst")
st.write("Ask research questions using historical financial data, current/recent market data, company reports, and an AI research agent.")

left, right = st.columns(2)
with left:
    amount = st.number_input("Investment amount (£, optional)", min_value=0.0, value=0.0, step=100.0)
    risk = st.selectbox("Risk preference", ["Not specified", "Lower risk", "Balanced", "Higher risk"])
with right:
    horizon = st.selectbox("Time horizon", ["Not specified", "Short term", "Medium term", "Long term"])
    st.caption("Examples: compare companies, ask about risks, or request a historical trend.")

question = st.text_area("Your research question", placeholder="Compare Microsoft and Apple as investments.", height=100)
if st.button("Analyze", type="primary"):
    if not question.strip():
        st.error("Please enter a research question.")
    else:
        payload = {"question": question.strip()}
        if amount > 0: payload["investment_amount"] = amount
        if risk != "Not specified": payload["risk_preference"] = risk.lower().replace(" risk", "")
        if horizon != "Not specified": payload["time_horizon"] = horizon.lower().replace(" term", "")
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
                    st.write(f"- {source.get('company_name', source.get('ticker', 'Company'))}: {source.get('document_name', 'Document')} — {source.get('source', 'Source unavailable')}")
            if result.get("tools_used"):
                st.subheader("Tools Used")
                st.write(", ".join(result["tools_used"]))
            if result.get("warnings"):
                st.subheader("Warnings")
                for warning in result["warnings"]: st.warning(warning)

st.divider()
st.caption("This application provides educational investment research and does not constitute personalised financial advice.")
