import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Chapada Advanced Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .card {
        background: black;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
        margin-bottom: 1rem;
    }
    .card-description {
        color: #666;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<h1 class="main-header">Chapada Advanced Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powerful analytics tools for data-driven decision making</p>', unsafe_allow_html=True)

# Features Grid
col1, col2 = st.columns(2)

with col1:
    with st.container():
        #st.markdown('<div class="card">', unsafe_allow_html=True)
        #st.markdown('<div class="feature-icon">📈</div>', unsafe_allow_html=True)
        st.markdown('<h3 class="card-title">📈 Parallel Coordinates</h3>', unsafe_allow_html=True)
        st.markdown('<p class="card-description">Interactive multidimensional data visualization. Explore complex datasets and identify patterns across multiple variables with our advanced parallel coordinates plot.</p>', unsafe_allow_html=True)
        
        if st.button("Launch Parallel Coordinates", key="parallel"):
            st.switch_page("pages/parallel.py")
        #st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        #st.markdown('<div class="card">', unsafe_allow_html=True)
        #st.markdown('<div class="feature-icon">🤖</div>', unsafe_allow_html=True)
        st.markdown('<h3 class="card-title">🧠 AI Genie Chat</h3>', unsafe_allow_html=True)
        st.markdown('<p class="card-description">Intelligent data assistant powered by AI Genie. Get instant insights, ask questions about your data from databricks, and receive intelligent recommendations.</p>', unsafe_allow_html=True)
        
        if st.button("Launch Genie Chat", key="chatbot"):
            st.switch_page("pages/chatbot.py")
        #st.markdown('</div>', unsafe_allow_html=True)

# Additional Information Section
st.markdown("---")
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.markdown("### 🔍 Data Exploration")
    st.markdown("""
    - Multi-dimensional analysis
    - Pattern recognition
    - Interactive filtering
    - Full data visualization
    """)

with col_info2:
    st.markdown("### 🎯 Smart Insights")
    st.markdown("""
    - AI-powered analytics
    - Natural language queries
    - Automated reporting
    - Predictive modeling
    """)

with col_info3:
    st.markdown("### ⚡ Performance")
    st.markdown("""
    - Real-time processing
    - Scalable architecture
    - Secure data handling
    - Cloud-ready deployment
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Chapada Advanced Analytics Platform • """ + str(datetime.now().year) + """</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.title("➤ Navigation")
    st.markdown("---")
    
    st.markdown("### Quick Access")
    if st.sidebar.button("📈 Parallel Coordinates", use_container_width=True):
        st.switch_page("pages/parallel.py")
    if st.sidebar.button("🧠 AI Genie", use_container_width=True):
        st.switch_page("pages/chatbot.py")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This platform provides advanced analytics capabilities for data exploration and AI Genie-powered insights.
    
    **Features include:**
    - Interactive visualizations
    - AI-driven analysis
    - Full data processing
    - Secure data handling
    """)