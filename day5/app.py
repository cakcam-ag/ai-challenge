"""
Day 5: Token Counting Frontend

Demonstrates token counting for different prompt lengths:
- Short prompt
- Long prompt  
- Prompt exceeding context limit
"""

import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Day 5 — Token Counting",
    page_icon="🔢",
    layout="wide",
)

# Global CSS for readability
st.markdown("""
<style>
    /* Main content area */
    .main { background-color: #ffffff; }
    .stApp { background-color: #ffffff; }
    
    /* Headers */
    h1, h2, h3, h4 { color: #000000 !important; }
    
    /* Main content text */
    .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
        color: #000000 !important;
    }
    
    /* Sidebar - ensure white text on dark background */
    .stSidebar {
        background-color: #262730;
    }
    .stSidebar .stMarkdown, 
    .stSidebar .stMarkdown p, 
    .stSidebar .stMarkdown li, 
    .stSidebar .stMarkdown span, 
    .stSidebar .stMarkdown div,
    .stSidebar .stMarkdown strong,
    .stSidebar .stMarkdown h2,
    .stSidebar .stMarkdown h3 {
        color: #ffffff !important;
    }
    
    /* Info boxes - make readable */
    .stAlert {
        background-color: #e3f2fd !important;
        border-left: 4px solid #2196f3 !important;
    }
    .stAlert .stMarkdown,
    .stAlert .stMarkdown p,
    .stAlert .stMarkdown span {
        color: #000000 !important;
    }
    
    /* Error boxes */
    .stAlert[data-baseweb="notification"][kind="error"] {
        background-color: #ffebee !important;
    }
    .stAlert[data-baseweb="notification"][kind="error"] .stMarkdown,
    .stAlert[data-baseweb="notification"][kind="error"] .stMarkdown p {
        color: #c62828 !important;
    }
    
    /* Warning boxes */
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background-color: #fff3e0 !important;
    }
    .stAlert[data-baseweb="notification"][kind="warning"] .stMarkdown,
    .stAlert[data-baseweb="notification"][kind="warning"] .stMarkdown p {
        color: #e65100 !important;
    }
    
    /* Info boxes (st.info) */
    .stAlert[data-baseweb="notification"][kind="info"] {
        background-color: #e3f2fd !important;
        border-left: 4px solid #2196f3 !important;
    }
    .stAlert[data-baseweb="notification"][kind="info"] .stMarkdown,
    .stAlert[data-baseweb="notification"][kind="info"] .stMarkdown p,
    .stAlert[data-baseweb="notification"][kind="info"] .stMarkdown span {
        color: #000000 !important;
    }
    
    /* Custom boxes */
    .token-metric {
        padding: 1rem;
        background-color: #f0f0f0;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #ffebee;
        border-radius: 0.5rem;
        border-left: 4px solid #d32f2f;
        margin: 0.5rem 0;
        color: #000000 !important;
    }
    .success-box {
        padding: 1rem;
        background-color: #e8f5e9;
        border-radius: 0.5rem;
        border-left: 4px solid #2e7d32;
        margin: 0.5rem 0;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000/analyze"

# Sidebar with instructions
with st.sidebar:
    st.markdown('<h2 style="color:#ffffff;">Day 5 – Token Counting</h2>', unsafe_allow_html=True)
    st.markdown(
        """
    <div style="color:#ffffff;">
    <p><strong>What are Tokens?</strong></p>
    <ul>
    <li>Tokens are pieces of text the model processes</li>
    <li>1 token ≈ 4 characters (English)</li>
    <li>Models have context limits (max tokens)</li>
    </ul>
    
    <p><strong>Three Test Cases:</strong></p>
    <ul>
    <li><strong>Short:</strong> Simple question (~50 tokens)</li>
    <li><strong>Long:</strong> Detailed request (~2000 tokens)</li>
    <li><strong>Exceeds Limit:</strong> Very long prompt that exceeds context window</li>
    </ul>
    
    <p><strong>What to Observe:</strong></p>
    <ul>
    <li>Token counts for input and output</li>
    <li>How model handles different lengths</li>
    <li>What happens when limit is exceeded</li>
    </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown('<h1 style="color:#000000;">🔢 Token Counting & Context Limits</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#000000;">Compare token usage across different prompt lengths and see how the model handles context limits.</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# Test case prompts
TEST_CASES = {
    "short": {
        "name": "Short Prompt",
        "prompt": "What is Python?",
        "model": "gpt-4o-mini",
        "description": "A simple, concise question (~50 tokens)",
    },
    "long": {
        "name": "Long Prompt",
        "prompt": """Write a comprehensive technical specification for a web application that allows users to:
1. Create and manage user accounts with authentication
2. Upload and store files in cloud storage
3. Process images using AI models for object detection
4. Generate reports based on user activity
5. Send email notifications for important events
6. Integrate with third-party APIs for payment processing
7. Provide real-time chat functionality between users
8. Support multiple languages and timezones
9. Implement role-based access control (RBAC)
10. Monitor system health and performance metrics

Please include:
- Detailed architecture diagrams
- Database schema design
- API endpoint specifications
- Security considerations
- Scalability requirements
- Deployment strategy
- Testing approach
- Cost estimation
- Timeline breakdown
- Risk assessment

Also explain how you would handle:
- High traffic scenarios (1M+ concurrent users)
- Data privacy compliance (GDPR, CCPA)
- Disaster recovery
- Load balancing
- Caching strategies
- Microservices vs monolith decision
- CI/CD pipeline setup
- Monitoring and alerting systems""",
        "model": "gpt-4o-mini",
        "description": "A detailed technical request (~2000 tokens)",
    },
    "exceeds_limit": {
        "name": "Exceeds Context Limit",
        "prompt": ("This is a test prompt designed to exceed the context limit. " * 1000) + 
                  ("Please write a comprehensive technical specification. " * 500) +
                  ("Include detailed documentation for all components. " * 500) +
                  ("Add extensive examples and use cases. " * 500) +
                  ("Provide thorough explanations for each section. " * 500),
        "model": "gpt-3.5-turbo",  # Smaller context window (16k) to make it easier to exceed
        "description": "A very long prompt that exceeds the model's context limit (~20k+ tokens)",
    },
}

# Model selection
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<h3 style="color:#000000;">📝 Test Cases</h3>', unsafe_allow_html=True)
with col2:
    selected_model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-5.1"],
        index=0,
    )

# Display test case buttons
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔹 Test: Short Prompt", use_container_width=True):
        st.session_state.test_case = "short"
        st.session_state.prompt = TEST_CASES["short"]["prompt"]
        st.session_state.model = TEST_CASES["short"]["model"]
        st.session_state.should_analyze = True
        st.rerun()

with col2:
    if st.button("🔸 Test: Long Prompt", use_container_width=True):
        st.session_state.test_case = "long"
        st.session_state.prompt = TEST_CASES["long"]["prompt"]
        st.session_state.model = TEST_CASES["long"]["model"]
        st.session_state.should_analyze = True
        st.rerun()

with col3:
    if st.button("🔴 Test: Exceeds Limit", use_container_width=True):
        st.session_state.test_case = "exceeds_limit"
        st.session_state.prompt = TEST_CASES["exceeds_limit"]["prompt"]
        st.session_state.model = TEST_CASES["exceeds_limit"]["model"]
        st.session_state.should_analyze = True
        st.rerun()

st.markdown("---")

# Initialize session state (must be before using it)
if "test_case" not in st.session_state:
    st.session_state.test_case = None
if "prompt" not in st.session_state:
    st.session_state.prompt = ""
if "model" not in st.session_state:
    st.session_state.model = selected_model
if "should_analyze" not in st.session_state:
    st.session_state.should_analyze = False

# Update model if changed
if selected_model != st.session_state.get("model"):
    st.session_state.model = selected_model

# Custom prompt input
st.markdown('<h3 style="color:#000000;">✏️ Or Enter Custom Prompt</h3>', unsafe_allow_html=True)
custom_prompt = st.text_area(
    "Enter your prompt:",
    value=st.session_state.get("prompt", ""),
    height=150,
    help="Type your own prompt to analyze token usage",
    key="prompt_input",
)

# Analyze button
analyze_clicked = st.button("🔍 Analyze Tokens", type="primary", use_container_width=True)

# If analyze button clicked, use custom prompt and trigger analysis
if analyze_clicked:
    if custom_prompt:
        st.session_state.prompt = custom_prompt
        st.session_state.test_case = "custom"
        st.session_state.should_analyze = True
        st.rerun()
    else:
        st.error("Please enter a prompt first!")

# Process analysis
if st.session_state.get("should_analyze"):
    prompt_to_use = st.session_state.get("prompt", "")
    test_case = st.session_state.get("test_case", "custom")
    model_to_use = st.session_state.get("model", selected_model)
    
    # Reset should_analyze flag to prevent re-triggering
    st.session_state.should_analyze = False

    if not prompt_to_use:
        st.error("Please enter a prompt or select a test case!")
    else:
        with st.spinner("Analyzing tokens and getting AI response..."):
            try:
                response = requests.post(
                    BACKEND_URL,
                    json={
                        "prompt": prompt_to_use,
                        "model": model_to_use,
                        "test_case": test_case,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data and data.get("exceeds_limit"):
                    st.markdown("---")
                    st.markdown(
                        f'<h3 style="color:#000000;">📊 Token Analysis Results</h3>',
                        unsafe_allow_html=True,
                    )

                    # Token metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Input Tokens", f"{data['input_tokens']:,}")
                    with col2:
                        st.metric("Context Limit", f"{data['context_limit']:,}")
                    with col3:
                        st.metric("Max Input Allowed", f"{data['max_input_tokens']:,}")
                    with col4:
                        st.metric(
                            "Usage %",
                            f"{data['token_usage_percentage']:.1f}%",
                            delta=f"{data['token_usage_percentage'] - 100:.1f}%",
                            delta_color="inverse",
                        )

                    # Error display
                    st.markdown(
                        f'<div class="error-box"><strong>❌ Error:</strong> {data["error"]}</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown("---")
                    st.markdown('<h4 style="color:#000000;">📝 Prompt (Preview)</h4>', unsafe_allow_html=True)
                    st.text_area("", prompt_to_use[:500] + "..." if len(prompt_to_use) > 500 else prompt_to_use, height=100, disabled=True)

                elif "error" in data:
                    st.error(f"Error: {data['error']}")
                else:
                    st.markdown("---")
                    st.markdown(
                        f'<h3 style="color:#000000;">📊 Token Analysis Results</h3>',
                        unsafe_allow_html=True,
                    )

                    # Token metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Input Tokens", f"{data['input_tokens']:,}")
                    with col2:
                        st.metric("Output Tokens", f"{data['output_tokens']:,}")
                    with col3:
                        st.metric("Total Tokens", f"{data['total_tokens']:,}")
                    with col4:
                        st.metric(
                            "Usage %",
                            f"{data['token_usage_percentage']:.1f}%",
                            delta=f"{100 - data['token_usage_percentage']:.1f}% remaining",
                        )

                    # Progress bar
                    st.progress(min(data["token_usage_percentage"] / 100, 1.0))
                    st.caption(f"Context limit: {data['context_limit']:,} tokens | Max input: {data['max_input_tokens']:,} tokens")

                    # API reported tokens (for comparison)
                    if "api_reported_tokens" in data:
                        st.markdown("---")
                        st.markdown('<h4 style="color:#000000;">🔍 API Reported Tokens (Verification)</h4>', unsafe_allow_html=True)
                        api_tokens = data["api_reported_tokens"]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Prompt Tokens (API)", f"{api_tokens['prompt_tokens']:,}")
                        with col2:
                            st.metric("Completion Tokens (API)", f"{api_tokens['completion_tokens']:,}")
                        with col3:
                            st.metric("Total Tokens (API)", f"{api_tokens['total_tokens']:,}")

                    # Response display
                    st.markdown("---")
                    st.markdown('<h4 style="color:#000000;">🤖 AI Response</h4>', unsafe_allow_html=True)
                    if data.get("response"):
                        st.markdown(
                            f'<div class="success-box">{data["response"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("No response generated.")

                    # Prompt preview
                    st.markdown("---")
                    st.markdown('<h4 style="color:#000000;">📝 Prompt (Preview)</h4>', unsafe_allow_html=True)
                    st.text_area("", prompt_to_use[:500] + "..." if len(prompt_to_use) > 500 else prompt_to_use, height=100, disabled=True)

                    # Analysis
                    st.markdown("---")
                    st.markdown('<h4 style="color:#000000;">📈 Analysis</h4>', unsafe_allow_html=True)
                    if data["input_tokens"] < 100:
                        analysis = "**Short Prompt:** Quick response, minimal token usage. Model processes efficiently."
                    elif data["input_tokens"] < 2000:
                        analysis = "**Long Prompt:** More context provided. Model has more information to work with, but uses more tokens."
                    else:
                        analysis = "**Very Long Prompt:** Significant token usage. Close to or at context limits."

                    if data.get("exceeds_limit"):
                        analysis += "\n\n⚠️ **Warning:** This prompt exceeds the model's context limit and cannot be processed."
                    elif data["token_usage_percentage"] > 90:
                        analysis += "\n\n⚠️ **Warning:** Very close to context limit. Consider reducing prompt length."
                    elif data["token_usage_percentage"] > 50:
                        analysis += "\n\n💡 **Note:** Using significant portion of context. Monitor token usage carefully."

                    st.markdown(f'<div style="color:#000000;">{analysis}</div>', unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure the Day 5 backend is running on port 8000.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

else:
    st.markdown(
        '<div style="padding: 1rem; background-color: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 0.5rem; color: #000000;">'
        '👆 Select a test case above or enter a custom prompt to analyze token usage.'
        '</div>',
        unsafe_allow_html=True
    )

