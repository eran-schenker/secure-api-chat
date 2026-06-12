import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables
load_dotenv()

st.set_page_config(page_title="🔒 Secure API Chat", layout="wide")

# 2. Check for API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Error: OPENAI_API_KEY not found in your .env file.")
    st.stop()

client = OpenAI()

# 3. Initialize multi-chat storage in memory
if "all_chats" not in st.session_state:
    st.session_state["all_chats"] = {
        "Chat 1": [
            {"role": "assistant", "content": "How can I help you analyze your data securely today?"}
        ]
    }

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = "Chat 1"

# 4. SIDEBAR: Chat History Manager
with st.sidebar:
    st.title("💬 Chat History")
    
    # Button to create a brand new chat
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_number = len(st.session_state["all_chats"]) + 1
        new_chat_name = f"Chat {new_chat_number}"
        
        st.session_state["all_chats"][new_chat_name] = [
            {"role": "assistant", "content": "Started a new secure session. What's on your mind?"}
        ]
        st.session_state["current_chat"] = new_chat_name
        st.rerun()
    
    st.write("---")
    
    # List all active chats as buttons
    for chat_name in list(st.session_state["all_chats"].keys()):
        is_active = (chat_name == st.session_state["current_chat"])
        
        if st.button(
            chat_name,
            key=f"btn_{chat_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state["current_chat"] = chat_name
            st.rerun()

# 5. MAIN CHAT WINDOW
active_chat = st.session_state["current_chat"]
st.title(f"🔒 Secure API Chat — {active_chat}")

# Display messages for the selected chat
for msg in st.session_state["all_chats"][active_chat]:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    st.chat_message(role).write(content)

# 6. Handle user input
if prompt := st.chat_input():
    # Append user prompt
    st.session_state["all_chats"][active_chat].append(
        {"role": "user", "content": prompt}
    )
    st.chat_message("user").write(prompt)

    # ---- Prevent runaway history (token + memory control)
    MAX_MESSAGES = 20
    history = st.session_state["all_chats"][active_chat]
    st.session_state["all_chats"][active_chat] = history[-MAX_MESSAGES:]

    # ---- API call with error handling + spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # "o4-mini"
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state["all_chats"][active_chat]
                )
                
                msg = response.choices[0].message.content or "⚠️ Empty response from model."
            
            except Exception as e:
                msg = f"⚠️ Error: {str(e)}"

            # Append assistant response
            st.session_state["all_chats"][active_chat].append(
                {"role": "assistant", "content": msg}
            )

            st.write(msg)