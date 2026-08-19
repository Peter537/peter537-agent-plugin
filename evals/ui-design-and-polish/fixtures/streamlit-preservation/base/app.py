import streamlit as st


def assign_selected() -> None:
    st.session_state["assignment_status"] = "Assigned"


st.set_page_config(page_title="Review queue", layout="wide")
st.title("Review queue")
queue = st.selectbox("Queue", ["Needs review", "Waiting"], key="queue_filter")
selected = st.dataframe(
    [{"id": "CASE-104", "summary": "Address evidence"}],
    key="review_table",
    on_select="rerun",
    selection_mode="single-row",
)
st.button("Assign to me", key="assign_action", on_click=assign_selected, disabled=not selected.selection.rows)
st.status(st.session_state.get("assignment_status", f"Showing {queue}"), expanded=False)
