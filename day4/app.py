"""
Day 4: Temperature Comparison Frontend

Compare AI responses at different temperature settings (0, 0.7, 1.2)
to see how accuracy, creativity, and diversity change.
"""

import streamlit as st
import requests

st.set_page_config(
    page_title="Day 4 — Temperature Comparison",
    page_icon="🌡️",
    layout="wide",
)

# Global CSS to ensure text is readable (light theme)
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    .stApp {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000/compare"

# Sidebar with instructions
with st.sidebar:
    st.markdown('<h2 style="color:#ffffff;">Day 4 – Temperature</h2>', unsafe_allow_html=True)
    st.markdown(
        """
    <div style="color:#ffffff;">
    <p><strong>What is Temperature?</strong></p>
    <ul>
    <li>Controls randomness in AI responses</li>
    <li>Lower = more deterministic, focused</li>
    <li>Higher = more creative, diverse</li>
    </ul>
    
    <p><strong>Temperature Values:</strong></p>
    <ul>
    <li><strong>0.0</strong>: Most accurate, deterministic, consistent</li>
    <li><strong>0.7</strong>: Balanced (default), good mix</li>
    <li><strong>1.5</strong>: More creative, diverse, less predictable</li>
    </ul>
    
    <p><strong>Best Use Cases:</strong></p>
    <ul>
    <li><strong>0.0</strong>: Factual Q&A, code generation, data extraction</li>
    <li><strong>0.7</strong>: General conversation, balanced tasks</li>
    <li><strong>1.5</strong>: Creative writing, brainstorming, ideation</li>
    </ul>
    </div>
    """,
        unsafe_allow_html=True
    )

st.markdown('<h1 style="color:#000000;">🌡️ Temperature Comparison</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#000000;">Enter a prompt below and see how different temperature settings affect the AI\'s response.</p>',
    unsafe_allow_html=True
)
st.markdown("---")

# Initialize session state
if "example_prompt" not in st.session_state:
    st.session_state.example_prompt = None
if "auto_compare" not in st.session_state:
    st.session_state.auto_compare = False

# Example prompts
st.markdown('<p style="color:#000000;"><strong>Quick examples (click to compare):</strong></p>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

example_clicked = None
with col1:
    if st.button("📚 Factual Question", use_container_width=True):
        example_clicked = "What is the capital of France and why is it significant?"
with col2:
    if st.button("💡 Creative Task", use_container_width=True):
        example_clicked = "Write a short creative story about a robot learning to paint."
with col3:
    if st.button("🔧 Technical Task", use_container_width=True):
        example_clicked = "Write a Python function to calculate the factorial of a number."

# Input prompt (manual entry)
st.markdown('<p style="color:#000000;"><strong>Or enter your own prompt:</strong></p>', unsafe_allow_html=True)
prompt = st.text_area(
    "Enter your prompt:",
    placeholder="e.g., 'Explain quantum computing in simple terms' or 'Write a creative story about a robot'",
    height=100,
    value=example_clicked if example_clicked else "",
)

# Manual compare button
compare_clicked = st.button("🚀 Compare Temperatures", type="primary", use_container_width=True)

# Determine which prompt to use
prompt_to_use = example_clicked if example_clicked else prompt

# Trigger comparison if button clicked or example selected
if compare_clicked or example_clicked:
    if not prompt_to_use:
        st.error("Please enter a prompt first!")
    else:
        with st.spinner("Running prompt with 3 different temperatures (this may take 10-20 seconds)..."):
            try:
                response = requests.post(
                    BACKEND_URL, json={"prompt": prompt_to_use}, timeout=120
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    st.error(f"Error: {data['error']}")
                else:
                    results = data["results"]

                    # Display results in 3 columns
                    st.markdown('<h3 style="color:#000000;">📊 Comparison Results</h3>', unsafe_allow_html=True)
                    st.markdown(f'<p style="color:#000000;"><strong>Prompt:</strong> {data["prompt"]}</p>', unsafe_allow_html=True)
                    st.markdown("---")

                    col1, col2, col3 = st.columns(3)

                    # Temperature 0.0
                    with col1:
                        temp_0 = results["temp_0.0"]
                        st.markdown(
                            '<h3 style="color:#000000;">🎯 Temperature 0.0</h3><p style="color:#666666;"><em>Deterministic & Accurate</em></p>',
                            unsafe_allow_html=True
                        )
                        st.info(f"**Tokens used:** {temp_0['tokens_used']}")
                        with st.container():
                            st.markdown(
                                f'<div style="padding:1rem;background-color:#ffffff;color:#000000;border-radius:0.5rem;border-left:4px solid #1f77b4;border:1px solid #e0e0e0;">{temp_0["response"]}</div>',
                                unsafe_allow_html=True,
                            )

                    # Temperature 0.7
                    with col2:
                        temp_07 = results["temp_0.7"]
                        st.markdown(
                            '<h3 style="color:#000000;">⚖️ Temperature 0.7</h3><p style="color:#666666;"><em>Balanced (Default)</em></p>',
                            unsafe_allow_html=True
                        )
                        st.info(f"**Tokens used:** {temp_07['tokens_used']}")
                        with st.container():
                            st.markdown(
                                f'<div style="padding:1rem;background-color:#ffffff;color:#000000;border-radius:0.5rem;border-left:4px solid #ff7f0e;border:1px solid #e0e0e0;">{temp_07["response"]}</div>',
                                unsafe_allow_html=True,
                            )

                    # Temperature 1.5
                    with col3:
                        temp_15 = results["temp_1.5"]
                        st.markdown(
                            '<h3 style="color:#000000;">🎨 Temperature 1.5</h3><p style="color:#666666;"><em>Creative & Diverse</em></p>',
                            unsafe_allow_html=True
                        )
                        st.info(f"**Tokens used:** {temp_15['tokens_used']}")
                        with st.container():
                            st.markdown(
                                f'<div style="padding:1rem;background-color:#ffffff;color:#000000;border-radius:0.5rem;border-left:4px solid #2ca02c;border:1px solid #e0e0e0;">{temp_15["response"]}</div>',
                                unsafe_allow_html=True,
                            )

                    # Analysis section
                    st.markdown("---")
                    st.markdown('<h3 style="color:#000000;">📈 Analysis</h3>', unsafe_allow_html=True)
                    st.markdown(
                        """
                    <div style="color:#000000;">
                    <p><strong>Observations:</strong></p>
                    <ul>
                    <li><strong>Temperature 0.0</strong>: Most consistent, factual, deterministic</li>
                    <li><strong>Temperature 0.7</strong>: Balanced between accuracy and creativity</li>
                    <li><strong>Temperature 1.5</strong>: More varied, creative, less predictable</li>
                    </ul>
                    
                    <p><strong>Which to use?</strong></p>
                    <ul>
                    <li><strong>0.0</strong>: Factual Q&A, code generation, data extraction</li>
                    <li><strong>0.7</strong>: General tasks, balanced responses</li>
                    <li><strong>1.5</strong>: Creative writing, brainstorming, ideation</li>
                    </ul>
                    </div>
                    """,
                        unsafe_allow_html=True
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot connect to backend. Make sure the Day 4 backend is running on port 8000."
                )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

