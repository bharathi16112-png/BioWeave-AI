import time
import streamlit as st


def render_agent_trace(profile_data, animate: bool = False):
    """
    Renders the multi-agent reasoning trace timeline.

    Parameters
    ----------
    profile_data : dict
        The full profile / pipeline output dict.
    animate : bool
        When True (live inference mode), each agent card fades-in
        sequentially with a short delay, making the pipeline feel real-time.
    """
    traces = profile_data.get("agent_trace", [])

    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 600;
                        color: #FFFFFF; font-size: 1.4rem;">
                Multi-Agent Reasoning Trace
            </h3>
            <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0;
                       font-family: 'Outfit', sans-serif;">
                Sequential audit trail of deep-learning pipeline decisions and milestone validations
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Outer container placeholder (used by animation) ───────────────────────
    container = st.empty()

    def _build_step_html(traces_subset: list) -> str:
        """Builds the full HTML card for the supplied subset of trace steps."""
        steps_html = ""
        for idx, trace in enumerate(traces_subset):
            agent_name = trace.get("agent_name", "Unknown Agent")
            status     = trace.get("status", "pending")
            duration   = trace.get("duration_ms", 0)
            task_desc  = trace.get("task", "")
            is_last    = (idx == len(traces_subset) - 1)

            status_color = "#A8FFB2" if status == "completed" else "#FFAF66"

            if status == "completed" and is_last:
                dot_style = (
                    "background-color: #00D2D3;"
                    "box-shadow: 0 0 0 3px rgba(0,210,211,0.35), 0 0 14px rgba(0,210,211,0.6);"
                )
            elif status == "completed":
                dot_style = "background-color: #00D2D3;"
            else:
                dot_style = "background-color: #0E1117; border-color: #505050;"

            step_border = (
                "border-bottom: 1px solid rgba(255,255,255,0.04); margin-bottom: 0;"
                if not is_last else ""
            )

            steps_html += f"""
            <div style="
                border-left: 2px solid rgba(0,210,211,0.35);
                padding-left: 22px;
                padding-bottom: 22px;
                position: relative;
                {step_border}
            ">
                <!-- Timeline dot -->
                <div style="
                    position: absolute;
                    left: -7px;
                    top: 4px;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 2px solid #00D2D3;
                    {dot_style}
                "></div>

                <!-- Header row -->
                <div style="display: flex; align-items: center;
                            justify-content: space-between; margin-bottom: 7px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-family: 'Outfit', sans-serif; font-weight: 700;
                                     color: #00D2D3; font-size: 1.05rem;">
                            {agent_name}
                        </span>
                        <span style="
                            background-color: rgba(0,210,211,0.1);
                            border: 1px solid rgba(0,210,211,0.3);
                            padding: 1px 7px;
                            border-radius: 4px;
                            font-family: 'Space Mono', monospace;
                            font-size: 0.68rem;
                            color: #00D2D3;
                            letter-spacing: 0.5px;
                        ">
                            AGENT {idx + 1}
                        </span>
                    </div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.78rem;
                                color: #707070; white-space: nowrap;">
                        <span style="color: #505050;">Duration:</span>
                        <span style="color: #00D2D3; font-weight: bold;"> {duration} ms</span>
                        &nbsp;&bull;&nbsp;
                        <span style="color: {status_color}; font-weight: bold;
                                     text-transform: uppercase; font-size: 0.72rem;
                                     letter-spacing: 0.5px;">
                            {status}
                        </span>
                    </div>
                </div>

                <!-- Task description -->
                <p style="
                    margin: 0;
                    font-size: 0.92rem;
                    line-height: 1.6;
                    color: #C9D1D9;
                    font-family: 'Outfit', sans-serif;
                ">
                    {task_desc}
                </p>
            </div>
            """
        return steps_html

    def _wrap_card(inner_html: str) -> str:
        return f"""
        <div style="
            background: rgba(22, 27, 34, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px 28px;
            margin-top: 4px;
        ">
            {inner_html}
        </div>
        """

    # ── Sequential reveal animation (live mode only) ───────────────────────────
    if animate and traces:
        for i in range(1, len(traces) + 1):
            # Show "running" spinner on the current agent
            subset = []
            for j, t in enumerate(traces):
                if j < i - 1:
                    subset.append(t)                        # already done
                elif j == i - 1:
                    # Mark the active agent as "running" while processing
                    running = dict(t)
                    running["status"] = "running"
                    subset.append(running)
                # future agents not shown yet

            container.html(_wrap_card(_build_step_html(subset)))
            time.sleep(0.55)   # pause so user sees each agent "execute"

            # Now mark it completed and flash the done state briefly
            subset[i - 1]["status"] = "completed"
            container.html(_wrap_card(_build_step_html(subset)))
            time.sleep(0.25)

        # Final render: all agents completed
        container.html(_wrap_card(_build_step_html(traces)))
    else:
        # Static render (mock-data mode or re-display of completed live result)
        container.html(_wrap_card(_build_step_html(traces)))
