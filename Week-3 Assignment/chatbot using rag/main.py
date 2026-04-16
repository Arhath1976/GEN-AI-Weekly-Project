from __future__ import annotations

from typing import List

import streamlit as st
from langchain_openai import ChatOpenAI
from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"
PREFERRED_MODELS = [
	"gpt-4.1-mini",
	"gpt-4o-mini",
	"gpt-4.1",
	"gpt-4o",
	"gpt-4-turbo",
	"gpt-3.5-turbo",
]


def initialize_state() -> None:
	if "messages" not in st.session_state:
		st.session_state.messages = []
	if "api_key" not in st.session_state:
		st.session_state.api_key = ""
	if "api_base" not in st.session_state:
		st.session_state.api_base = "https://api.openai.com/v1"
	if "active_model" not in st.session_state:
		st.session_state.active_model = DEFAULT_MODEL
	if "token_saver_mode" not in st.session_state:
		st.session_state.token_saver_mode = False
	if "show_token_saver_popup" not in st.session_state:
		st.session_state.show_token_saver_popup = False
	if "sidebar_expanded" not in st.session_state:
		st.session_state.sidebar_expanded = False
	if "app_closed" not in st.session_state:
		st.session_state.app_closed = False


def apply_styles() -> None:
	st.markdown(
		"""
<style>
* {
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
}

[data-testid="stMainBlockContainer"] {
	display: flex;
	flex-direction: column;
	padding-bottom: 7rem;
}

[data-testid="stAppViewContainer"] {
	background: linear-gradient(135deg, #0f1729 0%, #1a2847 25%, #0d1f40 50%, #0a1428 75%, #050a15 100%);
	background-attachment: fixed;
}

[data-testid="stHeader"] {
	background: transparent;
}

.title-row {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 1rem;
	margin-bottom: 2rem;
	margin-top: 0.5rem;
	padding-bottom: 1.5rem;
	border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.title-text {
	font-size: 2.5rem;
	font-weight: 900;
	letter-spacing: -0.01em;
	color: #e8eef8;
}

.model-pill {
	background: rgba(180, 217, 255, 0.12);
	color: #d7e5f7;
	padding: 0.4rem 0.9rem;
	border-radius: 999px;
	font-size: 0.75rem;
	font-weight: 600;
	letter-spacing: 0.5px;
	border: 1px solid rgba(180, 217, 255, 0.4);
}

[data-testid="stChatMessage"] {
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
	border: 1px solid rgba(255, 255, 255, 0.15);
	border-radius: 14px;
	backdrop-filter: blur(8px);
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
	margin-bottom: 0.75rem;
}

div[data-testid="stDialog"] {
	animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

div[data-testid="stDialog"] > div {
	border-radius: 20px;
	border: 1px solid rgba(200, 220, 255, 0.3);
	background: linear-gradient(145deg, rgba(15, 23, 41, 0.95), rgba(10, 20, 40, 0.96));
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
	backdrop-filter: blur(16px);
}

div[data-testid="stDialog"]::backdrop {
	background: rgba(2, 4, 10, 0.6);
	backdrop-filter: blur(8px);
}

.drawer-panel {
	min-height: calc(100vh - 180px);
	padding: 1rem;
	border: 1px solid rgba(180, 217, 255, 0.2);
	border-radius: 14px;
	background: linear-gradient(180deg, rgba(12, 20, 38, 0.6) 0%, rgba(8, 14, 30, 0.7) 100%);
}

.drawer-panel h4 {
	margin: 0;
	font-size: 1rem;
	letter-spacing: 0.03em;
	color: #e0ecff;
	text-transform: uppercase;
}

.drawer-panel button {
	background: linear-gradient(135deg, rgba(131, 180, 255, 0.15) 0%, rgba(100, 150, 220, 0.1) 100%) !important;
	border: 1px solid rgba(180, 217, 255, 0.3) !important;
	color: #e0ecff !important;
	border-radius: 10px !important;
	font-weight: 600 !important;
	transition: all 0.3s ease !important;
}

.drawer-panel button:hover {
	background: linear-gradient(135deg, rgba(131, 180, 255, 0.25) 0%, rgba(100, 150, 220, 0.15) 100%) !important;
	border-color: rgba(180, 217, 255, 0.5) !important;
	box-shadow: 0 4px 12px rgba(131, 180, 255, 0.2) !important;
}

[data-testid="stChatInputContainer"] {
	padding: 0.75rem 0 !important;
}

[data-testid="stChatInput"] {
	border-radius: 12px !important;
	border: 1px solid rgba(180, 217, 255, 0.25) !important;
	background: rgba(255, 255, 255, 0.04) !important;
	transition: all 0.3s ease !important;
}

[data-testid="stChatInput"]:focus {
	border-color: rgba(180, 217, 255, 0.5) !important;
	background: rgba(255, 255, 255, 0.08) !important;
	box-shadow: 0 0 12px rgba(131, 180, 255, 0.15) !important;
}

button[kind="primary"] {
	background: linear-gradient(135deg, #83b4ff 0%, #6495c8 100%) !important;
	color: #ffffff !important;
	border: none !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
	transition: all 0.3s ease !important;
	box-shadow: 0 4px 12px rgba(131, 180, 255, 0.3) !important;
}

button[kind="primary"]:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 6px 20px rgba(131, 180, 255, 0.4) !important;
}

button[kind="secondary"] {
	background: rgba(255, 255, 255, 0.08) !important;
	border: 1px solid rgba(255, 255, 255, 0.15) !important;
	color: #d9e9ff !important;
	border-radius: 10px !important;
	font-weight: 600 !important;
	transition: all 0.3s ease !important;
}

button[kind="secondary"]:hover {
	background: rgba(255, 255, 255, 0.12) !important;
	border-color: rgba(255, 255, 255, 0.25) !important;
}

input[type="password"], input[type="text"] {
	border-radius: 10px !important;
	border: 1px solid rgba(180, 217, 255, 0.25) !important;
	background: rgba(255, 255, 255, 0.04) !important;
	color: #ffffff !important;
	transition: all 0.3s ease !important;
}

input[type="password"]:focus, input[type="text"]:focus {
	border-color: rgba(180, 217, 255, 0.5) !important;
	background: rgba(255, 255, 255, 0.08) !important;
	box-shadow: 0 0 12px rgba(131, 180, 255, 0.15) !important;
}

.locked-bg {
	min-height: 68vh;
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.02);
	border: 1px solid rgba(255, 255, 255, 0.05);
	filter: blur(3px);
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

hr {
	border: none !important;
	border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
	margin: 1rem 0 !important;
}

	#drawer-toggle-anchor + div[data-testid="stButton"] {
		position: fixed;
		left: 82px;
		bottom: 58px;
		z-index: 1250;
		margin: 0 !important;
	}
</style>
""",
		unsafe_allow_html=True,
	)


def detect_model(api_key: str, api_base: str) -> str:
	try:
		client = OpenAI(api_key=api_key, base_url=api_base)
		available = [model.id for model in client.models.list().data]

		for preferred in PREFERRED_MODELS:
			if preferred in available:
				return preferred

		for model_name in available:
			if model_name.startswith("gpt") or model_name.startswith("meta") or model_name.startswith("claude"):
				return model_name

		if available:
			return available[0]
		
		return DEFAULT_MODEL
	except Exception as e:
		st.warning(f"Could not fetch models: {str(e)[:80]}")
		return DEFAULT_MODEL


@st.dialog("Token Saver Mode", width="medium")
def token_saver_popup() -> None:
	st.markdown("### ⚡ Token Saver Mode")
	st.caption("Optimized for reduced token consumption")
	st.markdown("")
	st.markdown(
		"When enabled, responses are optimized to be shorter and more concise, "
		"significantly reducing token usage from your API while maintaining quality."
	)
	current_state = "🟢 **Enabled**" if st.session_state.token_saver_mode else "🔴 **Disabled**"
	st.info(f"**Status:** {current_state}")


@st.dialog("Confirm Unlink", width="small")
def confirm_unlink_popup() -> None:
	st.warning("Are you sure you want to unlink this API key?")
	st.caption("This will end the current chat session and return to API linking.")
	col1, col2 = st.columns(2)
	with col1:
		if st.button("Cancel", use_container_width=True, key="unlink_cancel"):
			st.rerun()
	with col2:
		if st.button("Unlink", use_container_width=True, type="primary", key="unlink_confirm"):
			st.session_state.api_key = ""
			st.session_state.messages = []
			st.session_state.sidebar_expanded = False
			st.rerun()


def render_api_link_section() -> None:
	st.markdown("### 🔐 Connect your API Key")
	st.caption("Secure connection • No data stored • Premium experience")

	api_key_input = st.text_input("Enter your API key", type="password", placeholder="sk-...")
	if st.button("Continue", type="primary", use_container_width=True):
		api_key = api_key_input.strip()
		api_base = "https://api.openai.com/v1"

		if not api_key:
			st.error("Please enter an API key.")
			return

		try:
			with st.spinner("Detecting available models..."):
				model_name = detect_model(api_key, api_base)
		except Exception:
			st.error("Invalid key or network issue. Please check and try again.")
			return

		st.session_state.api_key = api_key
		st.session_state.api_base = api_base
		st.session_state.active_model = model_name
		st.rerun()

	st.divider()
	st.markdown(
		"""
<div style="display: flex; gap: 0.75rem; align-items: flex-start; padding: 1rem; background: linear-gradient(135deg, rgba(100, 150, 200, 0.08) 0%, rgba(80, 120, 180, 0.04) 100%); border-radius: 12px; border: 1px solid rgba(150, 200, 255, 0.15); border-left: 3px solid rgba(180, 217, 255, 0.4);">
	<span style="font-size: 1.25rem; color: #83b4ff; flex-shrink: 0;">ℹ️</span>
	<span style="font-size: 0.9rem; color: #d9e9ff; line-height: 1.6; font-weight: 500;">
		<strong style="color: #e0ecff;">Token Usage Notice:</strong> This application consumes tokens from your API key. Each message and response uses tokens, leading to potential exhaustion. 
		Enable <strong style="color: #83b4ff;">Token Saver Mode</strong> in chat to significantly reduce consumption.
	</span>
</div>
""",
		unsafe_allow_html=True,
	)


def render_title() -> None:
	model_name = st.session_state.active_model
	st.markdown(
		f"""
<div class="title-row">
	<div class="title-text">ChatBot Agent.ai</div>
	<div class="model-pill">{model_name}</div>
</div>
""",
		unsafe_allow_html=True,
	)


def toggle_sidebar() -> None:
	st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded


def on_token_saver_change() -> None:
	if st.session_state.token_saver_mode:
		st.session_state.show_token_saver_popup = True


def render_sidebar_controls() -> None:
	with st.container(border=True):
		st.markdown("#### Session Settings")
		st.checkbox(
			"token saver",
			key="token_saver_mode",
			on_change=on_token_saver_change,
			label_visibility="visible",
		)
		if st.session_state.show_token_saver_popup:
			st.session_state.show_token_saver_popup = False
			token_saver_popup()

		if st.button("🔌 End Session", use_container_width=True, key="end_session_btn"):
			st.session_state.app_closed = True
			st.session_state.sidebar_expanded = False
			st.rerun()

		if st.button("⛓ Unlink API", use_container_width=True, key="unlink_api_btn"):
			confirm_unlink_popup()

		st.divider()
		st.caption("ACTIVE MODEL")
		st.code(st.session_state.active_model, language=None)


def render_chat() -> None:
	for message in st.session_state.messages:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])

	prompt = st.chat_input("Type your message...")

	if not prompt:
		return

	st.session_state.messages.append({"role": "user", "content": prompt})

	system_prompt = "You are a helpful and concise AI assistant."
	if st.session_state.token_saver_mode:
		system_prompt += " Keep responses very brief and concise. Use 1-3 sentences. Avoid unnecessary details."

	llm = ChatOpenAI(
		api_key=st.session_state.api_key,
		base_url=st.session_state.api_base,
		model=st.session_state.active_model,
		temperature=0.3,
		max_tokens=250 if st.session_state.token_saver_mode else None,
	)

	conversation: List[dict] = [
		{"role": "system", "content": system_prompt}
	]
	conversation.extend(st.session_state.messages)

	with st.spinner("Thinking..."):
		response = llm.invoke(conversation)
		answer = response.content if isinstance(response.content, str) else str(response.content)

	st.session_state.messages.append({"role": "assistant", "content": answer})
	st.rerun()


def main() -> None:
	st.set_page_config(page_title="ChatBot Agent.ai", page_icon="🤖", layout="wide")
	initialize_state()
	apply_styles()

	if st.session_state.app_closed:
		st.title("Session Ended")
		st.info("This app session has been ended. Close this tab to fully exit.")
		st.stop()

	if not st.session_state.api_key:
		render_api_link_section()
		st.stop()

	st.markdown('<div id="drawer-toggle-anchor"></div>', unsafe_allow_html=True)
	toggle_icon = "<<<" if st.session_state.sidebar_expanded else ">>>"
	if st.button(toggle_icon, key="sidebar_toggle", type="secondary"):
		toggle_sidebar()
		st.rerun()

	render_title()
	if st.session_state.sidebar_expanded:
		left_col, main_col = st.columns([1, 3], gap="small")
		with left_col:
			render_sidebar_controls()
		with main_col:
			render_chat()
	else:
		render_chat()


if __name__ == "__main__":
	main()

