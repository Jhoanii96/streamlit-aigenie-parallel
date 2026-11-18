import os
import streamlit as st
import pandas as pd
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv 

load_dotenv(".env", override=True) 

# ---------------------------
# Page layout
# ---------------------------
st.set_page_config(page_title="Chapada Process Plant Space - Ask questions about your data", layout="wide")

SPACE_ID = os.getenv("GENIE_SPACE_ID")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

if not SPACE_ID:
    st.error("Missing Genie space id. Set GENIE_SPACE_ID in Streamlit secrets or environment variables.")

@st.cache_resource(show_spinner=False)
def get_client() -> WorkspaceClient:
    return WorkspaceClient()

w = get_client()

# ---------------------------
# Custom CSS for chat positioning and suggestions
# ---------------------------
st.markdown("""
<style>
    .stMarkdown {
        overflow-x: auto;
        width: 100%;
    }
    .suggestion-btn {
        width: 100%;
        text-align: left;
        padding: 12px;
        margin: 4px 0;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: transparent;
        cursor: pointer;
        transition: all 0.2s;
        white-space: normal;
        word-wrap: break-word;
    }
    .suggestion-btn:hover {
        background-color: #f8f9fa;
        border-color: #4285f4;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("➤ Navigation")
    st.markdown("---")
    
    st.markdown("### Quick Access")
    if st.sidebar.button("🏠︎ Home", use_container_width=True):
        st.switch_page("app.py")
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
    - Real-time processing
    - Secure data handling
    """)

st.header("Chapada Process Plant Space - Ask questions about your data")
st.markdown("###### Ask questions about your data in natural language")

# Session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestion_clicked" not in st.session_state:
    st.session_state.suggestion_clicked = None

# ---------------------------
# Suggested questions - Using Streamlit buttons instead
# ---------------------------
suggested_questions = [
    "What were our top 5 products by sales last month?",
    "Show me the sales trend for the last 6 months",
    "Which regions are performing above target?",
    "Compare this quarter's revenue with the previous quarter"
]

# Clear Chat button aligned to the far left
if st.session_state.messages or st.session_state.get('suggestion_clicked'):
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if st.button("Clear Chat", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ---------------------------
# Show suggestions if no messages - USING STREAMLIT BUTTONS
# ---------------------------
if not any(st.session_state.messages) and not st.session_state.get('suggestion_clicked'):
    with st.container():
        st.subheader("Try asking one of these questions:")

        # Create columns for the suggestions
        cols = st.columns(2)
        for i, question in enumerate(suggested_questions):
            with cols[i % 2]:
                if st.button(question, key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.suggestion_clicked = question
                    st.rerun()

# ---------------------------
# Chat history UI
# ---------------------------
for entry in st.session_state.messages:
    role = entry['type'] if entry['type'] else "none"

    if role == "user":
        col1, col2 = st.columns([0.3, 0.7])
        with col2:
            with st.chat_message("user"):
                st.write(entry['content'])
    elif role == "assistant":
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            with st.chat_message("assistant"):
                if entry['content']:
                    st.write(entry['content'])
                if not entry['data'].empty:
                    st.dataframe(entry['data'])




# ---------------------------
# Handle suggestion click
# ---------------------------
prompt = st.chat_input("Ask Genie a question…")

if st.session_state.suggestion_clicked:
    prompt = st.session_state.suggestion_clicked
    st.session_state.suggestion_clicked = None

# ---------------------------
# Send & display
# ---------------------------
if prompt and prompt.strip():  # Check for non-empty prompt
    # Add user message to session state
    st.session_state.messages.append({"type": "user", "content": prompt, "data": pd.DataFrame()})
    
    # Display user message
    col1, col2 = st.columns([0.3, 0.7])
    with col2:
        with st.chat_message("user"):
            st.write(prompt)

    # Display assistant response
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        with st.status("Contacting Genie…", expanded=False) as status:
            try:
                # Initialize response variables
                response = None
                text_result = None
                query_object = None
                data = None
                df = pd.DataFrame()
                content = ""
                
                # Get response from Genie
                if st.session_state.conversation_id is None:
                    response = w.genie.start_conversation_and_wait(
                        space_id=SPACE_ID, 
                        content=prompt
                    )
                    st.session_state.conversation_id = response.conversation_id
                else:
                    response = w.genie.create_message_and_wait(
                        space_id=SPACE_ID,
                        conversation_id=st.session_state.conversation_id,
                        content=prompt
                    )
                
                # Validate response
                if not response or not hasattr(response, 'attachments'):
                    raise ValueError("Invalid response from Genie API")
                
                # Process attachments
                if response.attachments:
                    attachments_object = response.attachments[0]
                    
                    # Extract text content
                    if hasattr(attachments_object, 'text') and attachments_object.text:
                        text_result = attachments_object.text
                        content = text_result.content if hasattr(text_result, 'content') else ""
                    
                    # Extract and execute query if present
                    if hasattr(attachments_object, 'query'):
                        query_object = attachments_object.query
                        
                        if query_object and hasattr(query_object, 'query'):
                            full_query = query_object.query
                            if full_query and full_query.strip():
                                data = w.statement_execution.execute_statement(
                                    warehouse_id=WAREHOUSE_ID, 
                                    statement=full_query
                                )
                
                status.update(label="Genie responded", state="complete", expanded=True)
                
                # Display assistant response
                with st.chat_message("assistant"):
                    if content:
                        st.write(content)
                    
                    # Display data if available
                    if query_object and data and hasattr(data, 'result'):
                        try:
                            if (hasattr(data, 'manifest') and 
                                hasattr(data.manifest, 'schema') and 
                                hasattr(data.manifest.schema, 'columns')):
                                
                                columns = [item.name for item in data.manifest.schema.columns]
                                
                                if (hasattr(data, 'result') and 
                                    hasattr(data.result, 'data_array') and 
                                    data.result.data_array):
                                    
                                    data_array = data.result.data_array
                                    df = pd.DataFrame(data_array, columns=columns)
                                    st.dataframe(df)
                                else:
                                    st.info("No data returned from query")
                            else:
                                st.warning("Invalid data structure in response")
                        except Exception as df_error:
                            st.error(f"Error processing data: {df_error}")
                
                # Add assistant response to session state
                st.session_state.messages.append({
                    "type": "assistant", 
                    "content": content, 
                    "data": df
                })
                
            except Exception as e:
                status.update(label="Request failed", state="error", expanded=True)
                error_msg = f"Error talking to Genie: {str(e)}"
                st.error(error_msg)
                
                # Log the error for debugging (optional)
                print(f"Genie API Error: {error_msg}")
                
                # Add error message to session state
                st.session_state.messages.append({
                    "type": "assistant", 
                    "content": f"Sorry, I encountered an error: {str(e)}", 
                    "data": pd.DataFrame()
                })

