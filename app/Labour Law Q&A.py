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

# --- Custom CSS for Clean Sidebar Navigation (Modified to insert title) ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    
    /* ------------------------------------------------------------- */
    /* FIX: Custom Title Insertion & Repositioning */
    /* ------------------------------------------------------------- */
    
    /* 1. Add the custom title via CSS content (Updated Content) */
    [data-testid="stSidebarNav"]::before {
        content: "Malaysian Labour Law Assistant";
        font-size: 1.5em; /* Matches h1 size */
        text-align: center;
        display: block;
        padding: 15px 0 10px 0;
        font-weight: bold;
    }
    
    /* 2. Add a separator line after the title */
    [data-testid="stSidebarNav"]::after {
        content: "";
        display: block;
        border-bottom: 1px solid #34495e; 
        margin-bottom: 10px;
    }
    
    /* 3. Hide the automatically generated title that we don't want */
    [data-testid="stSidebarNav"] > div:first-child > div:first-child {
        display: none;
    }

    /* 4. FIX: Use visibility: hidden instead of collapsing height to fix UI disappearance */
    /* This keeps the necessary container space but hides the placeholder content */
    [data-testid="stSidebar"] > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) {
        visibility: hidden;
        height: 0px; /* Still collapse height just in case, but rely on visibility */
    }

    /* High-Contrast Disclaimer Styling */
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


# --- Sidebar Setup (Simplified and Cleaned) ---
with st.sidebar:
    # 1. We must place SOMETHING here, but we hide it with CSS to clear the space.
    # The actual title is injected using the CSS ::before pseudo-element above.
    st.empty() 
    
    # NOTE: The navigation links are AUTO-GENERATED and now appear immediately
    # after the empty space, but the CSS places the title above them.

    
    # 3. Place the Legal Disclaimer at the bottom
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

    # Prepare history string
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
    
    # Retrieve AI output from "Final"
    row = response.rows[0]
    ai_response_obj = row.columns.get("Final")

    if ai_response_obj:
        ai_response_text = ai_response_obj.text
    else:
        ai_response_text = "⚠️ No response returned. Check JamAI column names."

    # Convert \n to newlines
    ai_response_text = ai_response_text.replace("\\n", "\n")

    # --- FIX: Keep indentation for sub-points ---
    def preserve_indentation(text: str):
        fixed_lines = []
        for line in text.split("\n"):
            # Replace leading spaces with &nbsp;
            leading_spaces = len(line) - len(line.lstrip(" "))
            fixed_line = "&nbsp;" * leading_spaces + line.lstrip(" ")
            fixed_lines.append(fixed_line)
        return "<br>".join(fixed_lines)

    safe_markdown = preserve_indentation(ai_response_text)

    # --- Stream by line, but preserve formatting ---
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

    # Save final answer to chat + history
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_response_text
    })

    st.session_state.conversation_history += f"Assistant: {ai_response_text}\n"

    st.stop()