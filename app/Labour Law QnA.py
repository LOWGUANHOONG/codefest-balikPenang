import streamlit as st
import time
from jamaibase import JamAI, types as t
import tempfile

JAMAI_API_KEY = st.secrets["JAMAI_API_KEY"]
JAMAI_PROJECT_ID = st.secrets["JAMAI_PROJECT_ID"]
jamai = JamAI(project_id=JAMAI_PROJECT_ID, token=JAMAI_API_KEY)


# --- Page navigation state ---
if "page" not in st.session_state:
    st.session_state.page = "Chat"  # default page

# --- Page setup ---
st.set_page_config(
    page_title="Malaysian Labour Law Assistant", 
    page_icon="⚖️",
    initial_sidebar_state="expanded", 
    layout="wide"
)


st.markdown("""
<style>
    .stApp {
        background-color: inherit;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    [data-testid="stSidebarNav"]::before {
        content: "Malaysian Labour Law Assistant";
        font-size: 1.5em; /* Matches h1 size */
        text-align: center;
        display: block;
        padding: 15px 0 10px 0;
        font-weight: bold;
    }
    
    [data-testid="stSidebarNav"]::after {
        content: "";
        display: block;
        border-bottom: 1px solid #34495e; 
        margin-bottom: 10px;
    }
    
    [data-testid="stSidebarNav"] > div:first-child > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) {
        visibility: hidden;
        height: 0px; /* Still collapse height just in case, but rely on visibility */
    }

    .disclaimer {
        background-color: #FFEE8C;
        padding: 15px;
        border-radius: 8px;
        font-size: 0.9em;
        color: #2c3e50;
        border-left: 5px solid #2c3e50;
        margin-top: 20px;
    }
    .disclaimer p, .disclaimer strong {
        font-weight: normal;
        color: #003747;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar Setup ---
with st.sidebar:
    st.empty() 

    st.markdown("""
    <div class="disclaimer">
        ⚠️ DISCLAIMER: This tool is for informational purposes only and does not constitute legal advice. 
        Always consult with a qualified legal professional for advice regarding specific legal issues.
    </div>
    """, unsafe_allow_html=True)

# --- Page: Chat ---

st.title("⚖️ Malaysian Labour Law Assistant")
st.subheader("💬 Labour Law Q&A Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI Assistant. How can I help you today?"}
    ]

# Persistent conversation history string for JamAI
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""  # <-- store full chat here

# Render chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input at the bottom
user_input = st.chat_input("Ask a question", key="input_box")

if user_input:
    # Store new user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Append to conversation history
    st.session_state.conversation_history += f"User: {user_input}\n"

    st.rerun()

# Process user input with JamAI
if st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    CHATBOT_ACTION_TABLE_ID = st.secrets["JAMAI_CHATBOT_ACTION_TABLE_ID"] # type: ignore

    history_text = st.session_state.conversation_history.strip()

    # ---- SEND to JamAI with History ----
    try:
        response = jamai.table.add_table_rows(
            table_type=t.TableType.ACTION,
            request=t.MultiRowAddRequest(
                table_id=CHATBOT_ACTION_TABLE_ID,
                data=[{
                    "User": history_text + user_query,
                }],
                stream=False
            )
        )
    except Exception as e:
        st.error(f"❌ JamAI API error: {e}")
        st.stop()
    
    row = response.rows[0]
    ai_response_obj = row.columns.get("Final")

    if ai_response_obj:
        ai_response_text = ai_response_obj.text
    else:
        ai_response_text = "⚠️ No response returned. Check JamAI column names."

    ai_response_text = ai_response_text.replace("\\n", "\n")

    def preserve_indentation(text: str):
        fixed_lines = []
        for line in text.split("\n"):
            leading_spaces = len(line) - len(line.lstrip(" "))
            fixed_line = "&nbsp;" * leading_spaces + line.lstrip(" ")
            fixed_lines.append(fixed_line)
        return "<br>".join(fixed_lines)

    safe_markdown = preserve_indentation(ai_response_text)

    with chat_container:
        with st.chat_message("assistant"):
            msg_box = st.empty()
            streamed_html = ""
            lines = safe_markdown.split("<br>")

            for line in lines:
                streamed_html += line + "<br>"
                msg_box.markdown(streamed_html + "▌", unsafe_allow_html=True)
                time.sleep(0.03)

            msg_box.markdown(streamed_html, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_response_text
    })

    st.session_state.conversation_history += f"Assistant: {ai_response_text}\n"

    st.stop()
