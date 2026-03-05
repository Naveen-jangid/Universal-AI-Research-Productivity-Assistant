"""
AI Agent page.
Autonomous multi-step research agent with tool-use, reasoning trace, and results.
"""

import streamlit as st
from frontend.utils.api_client import list_agent_tools, run_agent


def render() -> None:
    st.title("🤖 Autonomous AI Agent")
    st.markdown(
        "The AI agent can autonomously plan and execute multi-step research tasks. "
        "It uses tools like web search, document retrieval, calculator, and code execution "
        "to provide comprehensive, well-researched answers."
    )

    # ── Tools sidebar ─────────────────────────────────────────────────────
    with st.sidebar:
        st.subheader("🔧 Available Tools")
        try:
            tools_data = list_agent_tools()
            for tool in tools_data.get("tools", []):
                with st.expander(f"**{tool['name']}**"):
                    st.caption(tool["description"])
        except Exception:
            st.caption("Could not load tool list.")

        st.divider()
        use_memory = st.checkbox("Use Long-term Memory", value=True)

    # ── Agent interface ───────────────────────────────────────────────────
    if "agent_history" not in st.session_state:
        st.session_state["agent_history"] = []

    # Example tasks
    with st.expander("💡 Example Tasks"):
        examples = [
            "Research the latest advances in large language models and summarise key findings.",
            "What is the capital of France, and what is 2^10 + 5 * 3?",
            "Search for information about quantum computing and explain it simply.",
            "Analyse the documents in my knowledge base and provide a comprehensive summary.",
            "What is today's date, and calculate how many days until December 31st?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex[:20]}"):
                st.session_state["agent_task_input"] = ex

    # Task input
    task = st.text_area(
        "Describe the task for the agent:",
        value=st.session_state.get("agent_task_input", ""),
        height=120,
        placeholder="e.g., Research the latest AI developments and write a comprehensive summary...",
        key="agent_task_area",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        run_btn = st.button("🚀 Run Agent", type="primary", disabled=not task.strip())
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state["agent_history"] = []
            st.rerun()

    # Run agent
    if run_btn and task.strip():
        with st.status("🤖 Agent is working...", expanded=True) as status:
            st.write("Planning task execution...")
            try:
                result = run_agent(
                    task=task,
                    session_id=st.session_state.get("session_id"),
                    use_memory=use_memory,
                )

                # Show reasoning steps
                if result.get("steps"):
                    st.write(f"Completed {result['tool_calls']} tool calls:")
                    for step in result["steps"]:
                        st.write(f"  🔧 **{step['tool']}**: {str(step['input'])[:100]}")

                status.update(label="✅ Agent completed!", state="complete", expanded=False)

                st.session_state["agent_history"].append(
                    {
                        "task": task,
                        "result": result,
                    }
                )
                st.session_state.pop("agent_task_input", None)
            except Exception as e:
                status.update(label=f"❌ Agent failed: {e}", state="error")
                st.error(f"Error: {e}")

    # Display results
    for i, item in enumerate(reversed(st.session_state["agent_history"])):
        st.divider()
        st.markdown(f"**Task {len(st.session_state['agent_history']) - i}:** {item['task']}")

        result = item["result"]

        # Main answer
        st.subheader("📋 Result")
        st.markdown(result.get("output", "No output."))

        # Reasoning trace
        if result.get("steps"):
            with st.expander(f"🔍 Reasoning Trace ({result['tool_calls']} tool calls)"):
                for j, step in enumerate(result["steps"], 1):
                    st.markdown(f"**Step {j}: `{step['tool']}`**")
                    st.code(f"Input: {step['input']}", language="text")
                    st.code(f"Output: {step['output']}", language="text")
                    st.divider()
