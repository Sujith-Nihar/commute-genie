import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(page_title="CommuteGenie Singapore", page_icon="🚇", layout="wide")
st.title("🚇 CommuteGenie Singapore")
st.write("Multi-Agent AI Assistant for Singapore Public Transportation")

question = st.text_area(
    "Enter your transport question",
    placeholder="When is the next bus arriving at stop 83139?",
)

user_id = st.text_input("User ID", value="u_demo")

if st.button("Ask CommuteGenie"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        payload = {
            "question": question,
            "user_id": user_id,
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            st.subheader("Final Answer")
            st.success(data["answer"])

            st.subheader("Critic Approved")
            st.write(data["approved"])

            st.subheader("Used Agents")
            st.write(data["used_agents"])

            st.subheader("Trace")
            st.json(data["trace"])

        except Exception as exc:
            st.error(f"Request failed: {exc}")