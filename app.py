import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"
SUPPORTED_MODELS = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "o4-mini": (1.10, 4.40),
}


def model_label(model_id: str) -> str:
    input_price, output_price = SUPPORTED_MODELS[model_id]
    return f"{model_id} — ${input_price:.2f} in / ${output_price:.2f} out per 1M tokens"


def resolve_model(model_id: str | None) -> str:
    if model_id in SUPPORTED_MODELS:
        return model_id
    return DEFAULT_MODEL


# 1. Load environment variables
load_dotenv()

st.set_page_config(
    page_title="🔒 Secure API Chat",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Initialize multi-chat storage in memory
if "all_chats" not in st.session_state:
    st.session_state["all_chats"] = {
        "Chat 1": [
            {"role": "assistant", "content": "How can I help you analyze your data securely today?"}
        ]
    }

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = "Chat 1"

model_ids = list(SUPPORTED_MODELS.keys())

# 3. SIDEBAR: Model selector + chat history
with st.sidebar:
    st.subheader("🤖 Model")
    selected_model = st.selectbox(
        "OpenAI model",
        options=model_ids,
        index=model_ids.index(DEFAULT_MODEL),
        format_func=model_label,
        label_visibility="collapsed",
    )

    st.write("---")
    st.title("💬 Chat History")

    if st.button("➕ New Chat", use_container_width=True):
        new_chat_number = len(st.session_state["all_chats"]) + 1
        new_chat_name = f"Chat {new_chat_number}"

        st.session_state["all_chats"][new_chat_name] = [
            {"role": "assistant", "content": "Started a new secure session. What's on your mind?"}
        ]
        st.session_state["current_chat"] = new_chat_name
        st.rerun()

    st.write("---")

    for chat_name in list(st.session_state["all_chats"].keys()):
        is_active = chat_name == st.session_state["current_chat"]

        if st.button(
            chat_name,
            key=f"btn_{chat_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_chat"] = chat_name
            st.rerun()

# 4. Check for API key (after sidebar so controls stay visible)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Error: OPENAI_API_KEY not found in your .env file.")
    st.stop()

client = OpenAI()

# 5. MAIN CHAT WINDOW
active_chat = st.session_state["current_chat"]
model = resolve_model(selected_model)
st.title(f"🔒 Secure API Chat — {active_chat}")
st.caption(f"Using **{model}**")

for msg in st.session_state["all_chats"][active_chat]:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    st.chat_message(role).write(content)

# 6. Handle user input
if prompt := st.chat_input():
    st.session_state["all_chats"][active_chat].append(
        {"role": "user", "content": prompt}
    )
    st.chat_message("user").write(prompt)

    MAX_MESSAGES = 20
    history = st.session_state["all_chats"][active_chat]
    st.session_state["all_chats"][active_chat] = history[-MAX_MESSAGES:]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=st.session_state["all_chats"][active_chat],
                )

                msg = response.choices[0].message.content or "⚠️ Empty response from model."

            except Exception as e:
                msg = f"⚠️ Error: {str(e)}"

            st.session_state["all_chats"][active_chat].append(
                {"role": "assistant", "content": msg}
            )

            st.write(msg)
