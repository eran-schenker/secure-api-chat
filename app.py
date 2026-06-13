import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"
MAX_MESSAGES = 20
TRUNCATION_WARNING = (
    f"⚠️ This chat reached the {MAX_MESSAGES}-message limit. "
    "Oldest messages were removed — the model no longer sees them."
)
SUPPORTED_MODELS = {
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "benefit": "Fast and affordable for everyday chat and simple tasks.",
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "benefit": "Flagship multimodal model with the best balance of quality and speed.",
    },
    "gpt-4.1": {
        "input": 2.00,
        "output": 8.00,
        "benefit": "Strong instruction following with a 1M-token context window.",
    },
    "gpt-4.1-mini": {
        "input": 0.40,
        "output": 1.60,
        "benefit": "Lower cost with solid performance on focused tasks.",
    },
    "gpt-4.1-nano": {
        "input": 0.10,
        "output": 0.40,
        "benefit": "Cheapest option for classification, extraction, and simple prompts.",
    },
    "o4-mini": {
        "input": 1.10,
        "output": 4.40,
        "benefit": "Reasoning model for math, code, and multi-step problems.",
    },
    "o3-mini": {
        "input": 1.10,
        "output": 4.40,
        "benefit": "Cost-efficient reasoning for STEM, logic, and structured analysis.",
    },
    "o3": {
        "input": 10.00,
        "output": 40.00,
        "benefit": "Most capable reasoning model for complex, high-stakes analysis.",
    },
}


def resolve_model(model_id: str | None) -> str:
    if model_id in SUPPORTED_MODELS:
        return model_id
    return DEFAULT_MODEL


def to_api_messages(messages: list[dict]) -> list[dict]:
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def render_assistant_message(msg: dict) -> None:
    if msg.get("truncation_warning"):
        st.warning(TRUNCATION_WARNING)
    st.write(msg.get("content", ""))
    model_id = msg.get("model")
    if not model_id:
        return
    meta = SUPPORTED_MODELS.get(model_id, SUPPORTED_MODELS[DEFAULT_MODEL])
    name = msg.get("actual_model") or model_id
    st.caption(
        f"**{name}** · ${meta['input']:.2f} in / ${meta['output']:.2f} out per 1M tokens · {meta['benefit']}"
    )


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
        label_visibility="collapsed",
    )
    st.caption(SUPPORTED_MODELS[selected_model]["benefit"])

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

    can_delete = len(st.session_state["all_chats"]) > 1

    for chat_name in list(st.session_state["all_chats"].keys()):
        is_active = chat_name == st.session_state["current_chat"]
        chat_col, delete_col = st.columns([5, 1])

        with chat_col:
            if st.button(
                chat_name,
                key=f"btn_{chat_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["current_chat"] = chat_name
                st.rerun()

        with delete_col:
            if can_delete and st.button("🗑️", key=f"del_{chat_name}", help=f"Delete {chat_name}"):
                del st.session_state["all_chats"][chat_name]
                if st.session_state["current_chat"] == chat_name:
                    st.session_state["current_chat"] = next(iter(st.session_state["all_chats"]))
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

for msg in st.session_state["all_chats"][active_chat]:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    with st.chat_message(role):
        if role == "assistant":
            render_assistant_message(msg)
        else:
            st.write(content)

# 6. Handle user input
if prompt := st.chat_input():
    st.session_state["all_chats"][active_chat].append(
        {"role": "user", "content": prompt}
    )
    st.chat_message("user").write(prompt)

    history = st.session_state["all_chats"][active_chat]
    truncated = len(history) > MAX_MESSAGES
    st.session_state["all_chats"][active_chat] = history[-MAX_MESSAGES:]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_msg = {"role": "assistant", "content": "", "model": model}

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=to_api_messages(st.session_state["all_chats"][active_chat]),
                )

                assistant_msg["content"] = (
                    response.choices[0].message.content or "⚠️ Empty response from model."
                )
                assistant_msg["actual_model"] = response.model

            except Exception as e:
                assistant_msg["content"] = f"⚠️ Error: {str(e)}"

            if truncated:
                assistant_msg["truncation_warning"] = True

            st.session_state["all_chats"][active_chat].append(assistant_msg)
            render_assistant_message(assistant_msg)
