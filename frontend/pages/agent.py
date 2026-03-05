"""
AI Agent page.
Autonomous multi-step research agent with tool-use, reasoning trace, and results.
"""

import streamlit as st
from frontend.utils.api_client import list_agent_tools, run_agent


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>🤖 Autonomous AI Agent</h1>
            <p>Assign a complex research task. The agent plans, uses tools, and delivers a comprehensive result.</p>
            <span class="badge">Web Search · Doc Retrieval · Code Execution · Calculator</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tools sidebar ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.08em;padding:0.25rem 0 0.4rem;">Available Tools</div>',
            unsafe_allow_html=True,
        )
        try:
            tools_data = list_agent_tools()
            for tool in tools_data.get("tools", []):
                with st.expander(f"**{tool['name']}**"):
                    st.caption(tool["description"])
        except Exception:
            st.caption("Could not load tool list.")

        st.divider()
        use_memory = st.checkbox("Long-term Memory", value=True)

    if "agent_history" not in st.session_state:
        st.session_state["agent_history"] = []

    # ── Example tasks ─────────────────────────────────────────────────────
    with st.expander("💡 Example Tasks", expanded=len(st.session_state["agent_history"]) == 0):
        examples = [
            "Research the latest advances in large language models and summarise key findings.",
            "What is the capital of France, and what is 2^10 + 5 * 3?",
            "Search for information about quantum computing and explain it simply.",
            "Analyse the documents in my knowledge base and provide a comprehensive summary.",
            "What is today's date, and calculate how many days until December 31st?",
        ]
        cols = st.columns(2)
        for i, ex in enumerate(examples):
            with cols[i % 2]:
                if st.button(ex[:55] + "…" if len(ex) > 55 else ex, key=f"ex_{i}",
                             use_container_width=True):
                    st.session_state["agent_task_input"] = ex

    # ── Task input ────────────────────────────────────────────────────────
    task = st.text_area(
        "Describe the task for the agent:",
        value=st.session_state.get("agent_task_input", ""),
        height=100,
        placeholder="e.g., Research the latest AI developments and write a comprehensive summary…",
        key="agent_task_area",
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        run_btn = st.button("🚀 Run Agent", type="primary", disabled=not task.strip(),
                            use_container_width=True)
    with c2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state["agent_history"] = []
            st.rerun()

    # ── Execute ───────────────────────────────────────────────────────────
    if run_btn and task.strip():
        with st.status("🤖 Agent is working…", expanded=True) as status:
            st.write("Planning task execution…")
            try:
                result = run_agent(
                    task=task,
                    session_id=st.session_state.get("session_id"),
                    use_memory=use_memory,
                )
                if result.get("steps"):
                    st.write(f"Completed {result['tool_calls']} tool calls:")
                    for step in result["steps"]:
                        st.write(f"  🔧 **{step['tool']}**: {str(step['input'])[:100]}")

                status.update(label="✅ Agent completed!", state="complete", expanded=False)
                st.session_state["agent_history"].append({"task": task, "result": result})
                st.session_state.pop("agent_task_input", None)
            except Exception as e:
                status.update(label=f"❌ Agent failed: {e}", state="error")
                st.error(f"Error: {e}")

    # ── Results history ───────────────────────────────────────────────────
    for i, item in enumerate(reversed(st.session_state["agent_history"])):
        run_num = len(st.session_state["agent_history"]) - i
        result = item["result"]

        st.markdown(
            f'<div class="card card-accent" style="margin-top:1rem;">'
            f'<span style="color:#6366f1;font-weight:700;font-size:0.8rem;">RUN #{run_num}</span><br>'
            f'<span style="font-weight:600;">{item["task"][:120]}{"…" if len(item["task"])>120 else ""}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(result.get("output", "No output."))
        st.markdown("</div>", unsafe_allow_html=True)

        if result.get("steps"):
            with st.expander(f"🔍 Reasoning Trace ({result['tool_calls']} tool calls)"):
                for j, step in enumerate(result["steps"], 1):
                    st.markdown(
                        f'<div class="card" style="padding:0.65rem 1rem;margin:6px 0;">'
                        f'<span class="badge-purple">Step {j}</span>&nbsp;'
                        f'<code>{step["tool"]}</code></div>',
                        unsafe_allow_html=True,
                    )
                    c_in, c_out = st.columns(2)
                    with c_in:
                        st.code(f"Input: {step['input']}", language="text")
                    with c_out:
                        st.code(f"Output: {step['output']}", language="text")
