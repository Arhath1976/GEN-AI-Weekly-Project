import json
import os
import re
import smtplib
import sqlite3
import string
from datetime import datetime, timedelta
from email.message import EmailMessage
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import choice, token_hex
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="Agent.ai", layout="wide")


DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "agent_ai.db")

# Optional direct config: set these if you want credentials inside this file.
HARDCODED_GMAIL_EMAIL = "hareshgrownup@gmail.com"
HARDCODED_GMAIL_APP_PASSWORD = "usrb eapu turb blpy"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", HARDCODED_GMAIL_EMAIL)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", HARDCODED_GMAIL_APP_PASSWORD)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VERIFICATION_CODE_TTL_MINUTES = 10
PROVIDER_PRESETS = {
	"OpenAI": {
		"base_url": "https://api.openai.com/v1",
		"model": "gpt-4o-mini",
	},
	"Groq": {
		"base_url": "https://api.groq.com/openai/v1",
		"model": "llama-3.3-70b-versatile",
	},
	"OpenRouter": {
		"base_url": "https://openrouter.ai/api/v1",
		"model": "openai/gpt-4o-mini",
	},
	"Ollama": {
		"base_url": "http://localhost:11434/v1",
		"model": "llama3.2",
	},
	"Custom": {
		"base_url": DEFAULT_BASE_URL,
		"model": DEFAULT_MODEL,
	},
}


def get_database_connection() -> sqlite3.Connection:
	connection = sqlite3.connect(DATABASE_PATH)
	connection.row_factory = sqlite3.Row
	return connection


def ensure_user_table_column(connection: sqlite3.Connection, column_name: str, definition: str) -> None:
	columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
	if column_name not in columns:
		connection.execute(f"ALTER TABLE users ADD COLUMN {column_name} {definition}")


def initialize_database() -> None:
	with get_database_connection() as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE NOT NULL,
				display_name TEXT NOT NULL,
				email TEXT NOT NULL,
				bio TEXT DEFAULT '',
				password_hash TEXT NOT NULL,
				salt TEXT NOT NULL,
				is_verified INTEGER NOT NULL DEFAULT 0,
				verification_code TEXT DEFAULT '',
				verification_expires_at TEXT DEFAULT '',
				created_at TEXT DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		ensure_user_table_column(connection, "email", "TEXT DEFAULT ''")
		ensure_user_table_column(connection, "is_verified", "INTEGER NOT NULL DEFAULT 0")
		ensure_user_table_column(connection, "verification_code", "TEXT DEFAULT ''")
		ensure_user_table_column(connection, "verification_expires_at", "TEXT DEFAULT ''")


def hash_password(password: str, salt: str) -> str:
	password_bytes = password.encode("utf-8")
	salt_bytes = salt.encode("utf-8")
	derived = pbkdf2_hmac("sha256", password_bytes, salt_bytes, 100_000)
	return derived.hex()


def generate_verification_code() -> str:
	return "".join(choice(string.digits) for _ in range(6))


def get_verification_expiry() -> str:
	return (datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)).isoformat()


def is_valid_email(email: str) -> bool:
	return bool(EMAIL_PATTERN.fullmatch(email.strip().lower()))


def deliver_verification_code(email: str, display_name: str, verification_code: str) -> tuple[bool, str]:
	mail_host = SMTP_HOST
	mail_port = SMTP_PORT
	mail_username = SMTP_USERNAME
	mail_password = SMTP_PASSWORD
	mail_from = SMTP_FROM_EMAIL
	mail_use_tls = SMTP_USE_TLS

	# Gmail App Password shortcut: set GMAIL_EMAIL + GMAIL_APP_PASSWORD only.
	if not all([mail_host, mail_username, mail_password, mail_from]) and GMAIL_EMAIL and GMAIL_APP_PASSWORD:
		mail_host = "smtp.gmail.com"
		mail_port = 587
		mail_username = GMAIL_EMAIL
		mail_password = GMAIL_APP_PASSWORD
		mail_from = GMAIL_EMAIL
		mail_use_tls = True

	if not all([mail_host, mail_username, mail_password, mail_from]):
		return False, (
			"Email sender is not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD "
			f"(or SMTP_* settings). Built-in fallback code: {verification_code}"
		)

	message = EmailMessage()
	message["Subject"] = "Agent.ai verification code"
	message["From"] = mail_from
	message["To"] = email
	message.set_content(
		f"Hello {display_name},\n\n"
		f"Your Agent.ai verification code is: {verification_code}\n"
		f"This code expires in {VERIFICATION_CODE_TTL_MINUTES} minutes.\n\n"
		"If you did not request this account, ignore this email."
	)

	try:
		with smtplib.SMTP(mail_host, mail_port, timeout=20) as smtp:
			smtp.ehlo()
			if mail_use_tls:
				smtp.starttls()
				smtp.ehlo()
			smtp.login(mail_username, mail_password)
			smtp.send_message(message)
	except Exception as exc:
		return False, f"Email delivery failed. Built-in fallback code: {verification_code}. Error: {exc}"

	return True, f"Verification code sent to {email}."


def email_exists(email: str, exclude_user_id: int | None = None) -> bool:
	query = "SELECT id FROM users WHERE lower(email) = lower(?)"
	params: tuple[Any, ...] = (email.strip().lower(),)
	if exclude_user_id is not None:
		query += " AND id != ?"
		params = (email.strip().lower(), exclude_user_id)

	with get_database_connection() as connection:
		row = connection.execute(query, params).fetchone()
	return row is not None


def register_user(username: str, password: str, display_name: str, email: str, bio: str) -> tuple[bool, str]:
	clean_username = username.strip().lower()
	clean_display_name = display_name.strip()
	clean_email = email.strip().lower()
	clean_bio = bio.strip()

	if len(clean_username) < 3 or not clean_username.replace("_", "").isalnum():
		return False, "Username must be at least 3 characters and use letters, numbers, or underscores."
	if not is_valid_email(clean_email):
		return False, "Enter a valid email address."
	if email_exists(clean_email):
		return False, "That email is already registered."
	if len(password) < 8:
		return False, "Password must be at least 8 characters long."
	if not clean_display_name:
		return False, "Display name is required."

	salt = token_hex(16)
	password_hash = hash_password(password, salt)
	verification_code = generate_verification_code()
	verification_expires_at = get_verification_expiry()

	try:
		with get_database_connection() as connection:
			connection.execute(
				"""
				INSERT INTO users (
					username, display_name, email, bio, password_hash, salt, is_verified, verification_code, verification_expires_at
				)
				VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
				""",
				(
					clean_username,
					clean_display_name,
					clean_email,
					clean_bio,
					password_hash,
					salt,
					verification_code,
					verification_expires_at,
				),
			)
	except sqlite3.IntegrityError:
		return False, "That username already exists."

	_, delivery_message = deliver_verification_code(clean_email, clean_display_name, verification_code)
	return True, f"Account created successfully. {delivery_message}"


def build_public_user(user_row: dict[str, Any]) -> dict[str, Any]:
	return {
		"id": user_row["id"],
		"username": user_row["username"],
		"display_name": user_row["display_name"],
		"email": user_row["email"],
		"bio": user_row["bio"],
		"is_verified": bool(user_row["is_verified"]),
		"created_at": user_row["created_at"],
	}


def get_user_by_email(email: str) -> dict[str, Any] | None:
	with get_database_connection() as connection:
		row = connection.execute(
			"""
			SELECT id, username, display_name, email, bio, password_hash, salt, is_verified,
				verification_code, verification_expires_at, created_at
			FROM users
			WHERE lower(email) = lower(?)
			""",
			(email.strip().lower(),),
		).fetchone()
	return dict(row) if row else None


def authenticate_user(email: str, password: str) -> tuple[str, dict[str, Any] | None]:
	user = get_user_by_email(email)
	if not user:
		return "invalid", None

	computed_hash = hash_password(password, user["salt"])
	if not compare_digest(computed_hash, user["password_hash"]):
		return "invalid", None

	if not bool(user["is_verified"]):
		return "unverified", build_public_user(user)

	return "success", build_public_user(user)


def resend_verification_code(email: str) -> tuple[bool, str]:
	user = get_user_by_email(email)
	if user is None:
		return False, "No account exists for that email address."
	if bool(user["is_verified"]):
		return False, "This email is already verified."

	verification_code = generate_verification_code()
	verification_expires_at = get_verification_expiry()
	with get_database_connection() as connection:
		connection.execute(
			"UPDATE users SET verification_code = ?, verification_expires_at = ? WHERE id = ?",
			(verification_code, verification_expires_at, user["id"]),
		)

	_, delivery_message = deliver_verification_code(user["email"], user["display_name"], verification_code)
	return True, delivery_message


def verify_email_code(email: str, code: str) -> tuple[bool, str, dict[str, Any] | None]:
	user = get_user_by_email(email)
	if user is None:
		return False, "No account exists for that email address.", None
	if bool(user["is_verified"]):
		return True, "Email is already verified.", build_public_user(user)
	if user["verification_code"] != code.strip():
		return False, "Invalid verification code.", None
	if not user["verification_expires_at"]:
		return False, "No active verification code found. Request a new one.", None

	expires_at = datetime.fromisoformat(user["verification_expires_at"])
	if datetime.utcnow() > expires_at:
		return False, "Verification code expired. Request a new one.", None

	with get_database_connection() as connection:
		connection.execute(
			"""
			UPDATE users
			SET is_verified = 1, verification_code = '', verification_expires_at = ''
			WHERE id = ?
			""",
			(user["id"],),
		)

	verified_user = get_user_by_email(email)
	return True, "Email verified successfully.", build_public_user(verified_user)


def update_profile(user_id: int, display_name: str, bio: str) -> dict[str, Any]:
	clean_display_name = display_name.strip()
	clean_bio = bio.strip()

	if not clean_display_name:
		raise ValueError("Display name is required.")

	with get_database_connection() as connection:
		connection.execute(
			"UPDATE users SET display_name = ?, bio = ? WHERE id = ?",
			(clean_display_name, clean_bio, user_id),
		)
		row = connection.execute(
			"SELECT id, username, display_name, email, bio, is_verified, created_at FROM users WHERE id = ?",
			(user_id,),
		).fetchone()

	if row is None:
		raise ValueError("User profile could not be found.")

	return dict(row)


def detect_model_name(base_url: str, api_key: str, timeout_seconds: int = 15) -> tuple[str, str]:
	if not api_key.strip():
		return "", "API key is empty."

	models_url = base_url.strip().rstrip("/")
	if models_url.endswith("/v1"):
		models_url = f"{models_url}/models"
	elif not models_url.endswith("/models"):
		models_url = f"{models_url}/models"

	try:
		response = requests.get(
			models_url,
			headers={"Authorization": f"Bearer {api_key.strip()}", "Accept": "application/json"},
			timeout=timeout_seconds,
		)
		response.raise_for_status()
		data = response.json().get("data", [])
		model_ids = [item.get("id", "") for item in data if isinstance(item, dict) and item.get("id")]
		if not model_ids:
			return "", "No models found for this API key."

		preferred_models = [model for model in model_ids if model.lower().startswith("gpt")]
		detected = preferred_models[0] if preferred_models else model_ids[0]
		return detected, f"Model detected automatically: {detected}"
	except requests.RequestException as exc:
		return "", f"Could not detect model automatically: {exc}"


def infer_base_url_from_api_key(api_key: str, current_base_url: str) -> tuple[str, str]:
	clean_key = api_key.strip()
	if clean_key.startswith("sk-or-"):
		if current_base_url.strip().rstrip("/") != "https://openrouter.ai/api/v1":
			return "https://openrouter.ai/api/v1", "Detected OpenRouter key. Switched endpoint to OpenRouter automatically."
		return "https://openrouter.ai/api/v1", ""
	return current_base_url, ""


def clean_output_text(text: str) -> str:
	# Keep user-visible output clean by removing replacement/mojibake-style characters.
	cleaned = text.replace("\ufffd", "")
	cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", cleaned)
	return cleaned.strip()


def extract_affordable_tokens(error_text: str) -> int | None:
	match = re.search(r"can only afford\s+(\d+)", error_text, flags=re.IGNORECASE)
	if not match:
		return None
	return int(match.group(1))


def extract_prompt_token_limits(error_text: str) -> tuple[int, int] | None:
	match = re.search(
		r"Prompt tokens limit exceeded:\s*(\d+)\s*>\s*(\d+)",
		error_text,
		flags=re.IGNORECASE,
	)
	if not match:
		return None
	return int(match.group(1)), int(match.group(2))


def resolve_response_length_mode(selected_mode: str, user_prompt: str) -> str:
	if selected_mode != "Auto":
		return selected_mode

	prompt_text = user_prompt.strip().lower()
	word_count = len(prompt_text.split())
	long_cues = [
		"explain",
		"in detail",
		"step by step",
		"compare",
		"analysis",
		"pros and cons",
		"example",
		"guide",
	]
	short_cues = [
		"summarize",
		"short answer",
		"brief",
		"one line",
		"quick",
	]

	if any(cue in prompt_text for cue in short_cues) or word_count <= 8:
		return "Short"
	if any(cue in prompt_text for cue in long_cues) or word_count >= 18:
		return "Long"
	return "Medium"


def inject_cyberpunk_theme() -> None:
	st.markdown(
		"""
		<style>
		@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Rajdhani:wght@400;500;600;700&display=swap');

		:root {
			--bg-main: #f5f7fb;
			--bg-panel: #ffffff;
			--bg-soft: #eef2ff;
			--accent: #365df5;
			--accent-soft: #dfe7ff;
			--text-main: #1f2a44;
			--text-muted: #5e6c84;
			--border: #d9e0f2;
		}

		html, body, [class*="css"]  {
			font-family: 'Rajdhani', sans-serif;
			color: var(--text-main);
		}

		.stApp {
			background: linear-gradient(180deg, #f9fbff 0%, #f2f5fc 100%);
			color: var(--text-main);
		}

		[data-testid="stAppViewContainer"] > .main,
		[data-testid="stSidebar"] > div:first-child {
			background: transparent;
		}

		[data-testid="stHeader"] {
			background: rgba(255, 255, 255, 0.65);
		}

		[data-testid="stSidebar"] {
			border-right: 1px solid var(--border);
			background: var(--bg-panel);
			box-shadow: 0 0 24px rgba(31, 42, 68, 0.06);
		}

		[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
		[data-testid="stSidebar"] label,
		[data-testid="stSidebar"] span,
		[data-testid="stSidebar"] div {
			color: var(--text-main);
		}

		.block-container {
			padding-top: 2rem;
			position: relative;
			z-index: 1;
		}

		.cyber-shell {
			padding: 1.4rem 1.6rem;
			margin-bottom: 1.2rem;
			background: #ffffff;
			border: 1px solid var(--border);
			border-radius: 12px;
			box-shadow: 0 8px 24px rgba(31, 42, 68, 0.06);
		}

		.cyber-eyebrow {
			font-family: 'Orbitron', sans-serif;
			font-size: 0.88rem;
			letter-spacing: 0.12rem;
			text-transform: uppercase;
			color: var(--accent);
			margin-bottom: 0.3rem;
		}

		.cyber-title {
			font-family: 'Orbitron', sans-serif;
			font-size: 2.4rem;
			font-weight: 800;
			letter-spacing: 0.05rem;
			line-height: 1;
			text-transform: uppercase;
			color: #2b3a67;
			margin: 0;
		}

		.cyber-subtitle {
			margin-top: 0.6rem;
			color: var(--text-muted);
			font-size: 1.1rem;
			max-width: 760px;
		}

		.cyber-status-bar {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
			gap: 0.8rem;
			margin-top: 1.1rem;
		}

		.cyber-model-line {
			margin-top: 0.9rem;
			font-family: 'Orbitron', sans-serif;
			font-size: 0.92rem;
			letter-spacing: 0.06rem;
			color: var(--accent);
		}

		.cyber-stat {
			background: var(--bg-soft);
			border: 1px solid var(--accent-soft);
			padding: 0.8rem 0.95rem;
			border-radius: 8px;
		}

		.cyber-stat-label {
			font-family: 'Orbitron', sans-serif;
			font-size: 0.72rem;
			letter-spacing: 0.12rem;
			text-transform: uppercase;
			color: var(--accent);
		}

		.cyber-stat-value {
			font-size: 1.1rem;
			font-weight: 700;
			color: var(--text-main);
			margin-top: 0.18rem;
		}

		h1, h2, h3 {
			font-family: 'Orbitron', sans-serif;
			text-transform: uppercase;
			letter-spacing: 0.06rem;
			color: #2b3a67;
		}

		[data-testid="stChatMessage"] {
			background: #ffffff;
			border: 1px solid var(--border);
			border-radius: 10px;
			margin-bottom: 0.9rem;
			padding: 0.5rem 0.4rem;
			box-shadow: 0 4px 14px rgba(31, 42, 68, 0.05);
		}

		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
			font-size: 1.1rem;
			line-height: 1.55;
		}

		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div,
		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
		[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
			color: var(--text-main) !important;
			opacity: 1 !important;
		}

		[data-testid="stChatInput"] {
			background: #ffffff;
			border: 1px solid var(--border);
			box-shadow: 0 -8px 20px rgba(31, 42, 68, 0.08);
			border-radius: 10px;
		}

		.stTextInput input,
		.stTextArea textarea,
		.stSelectbox div[data-baseweb="select"] > div,
		.stNumberInput input {
			background: #ffffff;
			color: var(--text-main);
			border: 1px solid var(--border);
			border-radius: 8px;
		}

		.stTextInput input:disabled,
		.stTextArea textarea:disabled {
			color: #1f2a44 !important;
			-webkit-text-fill-color: #1f2a44 !important;
			opacity: 1 !important;
		}

		.stSlider [data-baseweb="slider"] > div > div {
			background: var(--accent);
		}

		.stButton > button,
		.stDownloadButton > button,
		.stFormSubmitButton > button {
			font-family: 'Orbitron', sans-serif;
			text-transform: uppercase;
			letter-spacing: 0.08rem;
			background: linear-gradient(90deg, #4568ff, #5b7cff);
			color: #ffffff !important;
			border: none;
			border-radius: 8px;
			box-shadow: 0 8px 18px rgba(54, 93, 245, 0.24);
			font-weight: 700;
		}

		.stButton > button:hover,
		.stFormSubmitButton > button:hover {
			background: linear-gradient(90deg, #365df5, #4d71ff);
			color: #ffffff !important;
		}

		.stButton > button:disabled,
		.stFormSubmitButton > button:disabled {
			opacity: 0.65;
			color: #e8edff !important;
		}

		.stToggle label div[data-testid="stMarkdownContainer"] p,
		.stCaption,
		small {
			color: var(--text-muted) !important;
		}

		/* Make toggle labels and switch controls high-contrast and fully visible. */
		.stToggle label div[data-testid="stMarkdownContainer"] p {
			color: #243559 !important;
			opacity: 1 !important;
			font-weight: 700 !important;
		}

		.stToggle [data-baseweb="checkbox"] > div {
			background-color: #d5def8 !important;
			opacity: 1 !important;
		}

		.stToggle [data-baseweb="checkbox"] > div[aria-checked="true"] {
			background-color: #365df5 !important;
		}

		.stToggle [data-baseweb="checkbox"] > div > div {
			background-color: #ffffff !important;
		}

		label,
		[data-testid="stWidgetLabel"],
		[data-testid="stWidgetLabel"] p,
		[data-testid="stTextInputRootElement"] label,
		[data-testid="stTextAreaRootElement"] label,
		[data-testid="stForm"] label,
		[data-testid="stForm"] [data-testid="stWidgetLabel"] p {
			color: #364766 !important;
			opacity: 1 !important;
			font-weight: 600 !important;
		}

		.stAlert {
			border-radius: 8px;
			border: 1px solid var(--border);
		}

		[data-testid="collapsedControl"] button,
		[data-testid="stSidebarCollapsedControl"] button,
		[data-testid="stHeader"] button[aria-label*="sidebar" i],
		[data-testid="stHeader"] button[title*="sidebar" i],
		[data-testid="stHeader"] button[kind="headerNoPadding"] {
			background: #365df5 !important;
			color: #ffffff !important;
			border: 1px solid #2f52d6 !important;
			border-radius: 8px !important;
			box-shadow: 0 6px 14px rgba(54, 93, 245, 0.24) !important;
			opacity: 1 !important;
		}

		[data-testid="collapsedControl"] button:hover,
		[data-testid="stSidebarCollapsedControl"] button:hover,
		[data-testid="stHeader"] button[aria-label*="sidebar" i]:hover,
		[data-testid="stHeader"] button[title*="sidebar" i]:hover,
		[data-testid="stHeader"] button[kind="headerNoPadding"]:hover {
			background: #2f52d6 !important;
		}

		[data-testid="collapsedControl"] button svg,
		[data-testid="stSidebarCollapsedControl"] button svg,
		[data-testid="stHeader"] button[aria-label*="sidebar" i] svg,
		[data-testid="stHeader"] button[title*="sidebar" i] svg,
		[data-testid="stHeader"] button[kind="headerNoPadding"] svg {
			fill: #ffffff !important;
			stroke: #ffffff !important;
			color: #ffffff !important;
			opacity: 1 !important;
		}

		.floating-help {
			position: fixed;
			right: 22px;
			bottom: 98px;
			z-index: 100000;
		}

		.floating-help-icon {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			width: 34px;
			height: 34px;
			border-radius: 50%;
			background: #365df5;
			color: #ffffff;
			font-family: 'Orbitron', sans-serif;
			font-weight: 700;
			cursor: default;
			box-shadow: 0 8px 18px rgba(54, 93, 245, 0.24);
		}

		.floating-help-tooltip {
			position: absolute;
			right: 44px;
			bottom: 0;
			width: 255px;
			padding: 0.6rem 0.75rem;
			border-radius: 8px;
			background: #1f2a44;
			color: #ffffff;
			font-size: 0.95rem;
			line-height: 1.3;
			box-shadow: 0 12px 22px rgba(31, 42, 68, 0.26);
			opacity: 0;
			transform: translateY(6px);
			pointer-events: none;
			transition: opacity 0.18s ease, transform 0.18s ease;
		}

		.floating-help:hover .floating-help-tooltip {
			opacity: 1;
			transform: translateY(0);
		}

		@media (max-width: 780px) {
			.cyber-title {
				font-size: 1.85rem;
			}

			.cyber-shell {
				padding: 1rem;
			}

			.floating-help {
				right: 12px;
				bottom: 86px;
			}

			.floating-help-tooltip {
				width: 215px;
				right: 40px;
			}
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def render_floating_help() -> None:
	st.markdown(
		"""
		<div
			title="This is an API tester app. Link your API key and start right away."
			style="position: fixed; right: 22px; bottom: 148px; z-index: 2147483647;"
		>
			<div
				style="display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 50%; background: #365df5; color: #ffffff; font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 15px; box-shadow: 0 8px 18px rgba(54, 93, 245, 0.24);"
			>
				?
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def render_header(model: str, api_key: str) -> None:
	model_label = model.strip() if api_key.strip() and model.strip() else "No model detected"
	st.markdown(
		f"""
		<div class="cyber-shell">
			<div class="cyber-eyebrow">Workspace Console</div>
			<h1 class="cyber-title">Agent.ai</h1>
			<div class="cyber-subtitle">
				A clean chat workspace for OpenAI-compatible models with simple account access
				and organized provider configuration.
			</div>
			<div class="cyber-model-line">Model = {model_label}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def initialize_state() -> None:
	if "messages" not in st.session_state:
		st.session_state.messages = [
			{
				"role": "assistant",
				"content": "Hello. Configure your provider in the sidebar and ask a question.",
			}
		]
	if "provider_name" not in st.session_state:
		st.session_state.provider_name = "OpenAI"
	if "base_url_value" not in st.session_state:
		st.session_state.base_url_value = DEFAULT_BASE_URL
	if "model_value" not in st.session_state:
		st.session_state.model_value = DEFAULT_MODEL
	if "api_key_value" not in st.session_state:
		st.session_state.api_key_value = DEFAULT_API_KEY
	if "system_prompt_value" not in st.session_state:
		st.session_state.system_prompt_value = "You are a helpful AI assistant."
	if "temperature_value" not in st.session_state:
		st.session_state.temperature_value = 0.7
	if "max_tokens_value" not in st.session_state:
		st.session_state.max_tokens_value = 512
	if "response_length_value" not in st.session_state:
		st.session_state.response_length_value = "Auto"
	if "token_saver_mode_value" not in st.session_state:
		st.session_state.token_saver_mode_value = False
	if "unlimited_output_value" not in st.session_state:
		st.session_state.unlimited_output_value = True
	if "credit_cap_tokens_value" not in st.session_state:
		st.session_state.credit_cap_tokens_value = 0
	if "timeout_seconds_value" not in st.session_state:
		st.session_state.timeout_seconds_value = 60
	if "use_streaming_value" not in st.session_state:
		st.session_state.use_streaming_value = True
	if "current_user" not in st.session_state:
		st.session_state.current_user = None
	if "auth_view" not in st.session_state:
		st.session_state.auth_view = "login"
	if "verification_email_value" not in st.session_state:
		st.session_state.verification_email_value = ""
	if "verification_delivery_notice" not in st.session_state:
		st.session_state.verification_delivery_notice = ""
	if "auth_notice" not in st.session_state:
		st.session_state.auth_notice = ""
	if "sidebar_notice" not in st.session_state:
		st.session_state.sidebar_notice = ""
	if "settings_panel_value" not in st.session_state:
		st.session_state.settings_panel_value = "Profile"
	if "pending_settings_panel" not in st.session_state:
		st.session_state.pending_settings_panel = ""
	if "model_detection_fingerprint" not in st.session_state:
		st.session_state.model_detection_fingerprint = ""


def apply_provider_preset(provider_name: str) -> None:
	preset = PROVIDER_PRESETS[provider_name]
	st.session_state.provider_name = provider_name
	st.session_state.base_url_value = preset["base_url"]
	st.session_state.model_value = preset["model"]


def logout_user() -> None:
	st.session_state.current_user = None
	st.session_state.auth_view = "login"
	st.session_state.messages = [
		{
			"role": "assistant",
			"content": "Hello. Sign in with a verified email to access Agent.ai and start a new session.",
		}
	]


def render_account_controls() -> None:
	current_user = st.session_state.current_user
	if current_user is None:
		st.markdown("### Login")
		if st.session_state.auth_notice:
			st.success(st.session_state.auth_notice)
			st.session_state.auth_notice = ""
		with st.form("login_form", clear_on_submit=False):
			email = st.text_input("Email", key="login_email")
			password = st.text_input("Password", type="password", key="login_password")
			if st.form_submit_button("Login", use_container_width=True):
				status, user = authenticate_user(email, password)
				if status == "invalid":
					st.error("Invalid email or password.")
				elif status == "unverified":
					st.session_state.verification_email_value = email.strip().lower()
					st.session_state.auth_view = "verify"
					st.rerun()
				else:
					st.session_state.current_user = user
					st.session_state.auth_view = "login"
					st.session_state.messages = [
						{
							"role": "assistant",
							"content": f"Welcome back, {user['display_name']}. Your access layer is active.",
						}
					]
					st.rerun()
		st.caption("New user?")
		if st.button("Create account", use_container_width=True):
			st.session_state.auth_view = "register"
			st.rerun()
		return

	st.markdown(f"**Operator:** {current_user['display_name']}")
	st.caption(f"{current_user['email']} | @{current_user['username']}")
	st.caption("Email verified")
	if current_user.get("bio"):
		st.caption(current_user["bio"])
	if st.button("Logout", use_container_width=True):
		logout_user()
		st.rerun()


def render_register_page() -> None:
	st.markdown("## Create New Account")
	st.caption("Create your account, then verify your email before logging in.")

	with st.form("register_form", clear_on_submit=False):
		display_name = st.text_input(
			"Display name",
			key="register_display_name",
			placeholder="Example: John Mathew",
		)
		username = st.text_input(
			"Username",
			key="register_username",
			placeholder="Example: john_mathew",
		)
		email = st.text_input(
			"Email",
			key="register_email",
			placeholder="Example: yourname@gmail.com",
		)
		bio = st.text_area(
			"Short bio",
			key="register_bio",
			height=90,
			placeholder="Optional: Tell us briefly about yourself",
		)
		password = st.text_input(
			"Password",
			type="password",
			key="register_password",
			placeholder="At least 8 characters",
		)
		confirm_password = st.text_input(
			"Confirm password",
			type="password",
			key="register_confirm_password",
			placeholder="Re-enter the same password",
		)
		if st.form_submit_button("Create Account", use_container_width=True):
			if password != confirm_password:
				st.error("Passwords do not match.")
			else:
				existing_user = get_user_by_email(email)
				if existing_user is not None:
					if bool(existing_user["is_verified"]):
						st.error("An account with this email already exists. Please log in.")
					else:
						resend_ok, resend_message = resend_verification_code(email)
						st.session_state.verification_email_value = email.strip().lower()
						st.session_state.verification_delivery_notice = resend_message
						st.session_state.auth_view = "verify"
						if resend_ok:
							st.success("Account already exists but is not verified. A fresh verification code has been sent.")
						else:
							st.warning("Account exists but is not verified. Continue with verification using your latest code.")
						st.rerun()
						return
				success, message = register_user(username, password, display_name, email, bio)
				if not success:
					st.error(message)
				else:
					st.session_state.verification_email_value = email.strip().lower()
					st.session_state.verification_delivery_notice = message
					st.session_state.auth_view = "verify"
					st.rerun()

	if st.button("Back to login", key="register_back_login"):
		st.session_state.auth_view = "login"
		st.rerun()


def render_verify_page() -> None:
	st.markdown("## Verify Email")
	st.caption("Enter the verification code sent to your email.")
	st.caption("Tip: Set GMAIL_EMAIL and GMAIL_APP_PASSWORD to send real emails via Gmail.")
	if st.session_state.verification_delivery_notice:
		if "Built-in fallback code:" in st.session_state.verification_delivery_notice:
			st.warning(st.session_state.verification_delivery_notice)
		else:
			st.info(st.session_state.verification_delivery_notice)

	if st.session_state.verification_email_value:
		verification_email = st.text_input(
			"Verification email",
			value=st.session_state.verification_email_value,
			disabled=True,
		)
	else:
		verification_email = st.text_input(
			"Verification email",
			key="verification_email_value",
			placeholder="Enter your account email",
		)

	with st.form("verify_email_form", clear_on_submit=False):
		verification_code = st.text_input("Verification code", max_chars=6, key="verification_code_input")
		if st.form_submit_button("Verify Email", use_container_width=True):
			success, message, _ = verify_email_code(verification_email, verification_code)
			if not success:
				st.error(message)
			else:
				st.session_state.auth_view = "login"
				st.session_state.auth_notice = "Account has been created and verified. Please login."
				st.session_state.verification_delivery_notice = ""
				st.success(message)
				st.rerun()

	if st.button("Resend verification code", key="verify_resend"):
		success, message = resend_verification_code(verification_email)
		if success:
			st.session_state.verification_delivery_notice = message
			st.rerun()
		else:
			st.error(message)

	if st.button("Back to login", key="verify_back_login"):
		st.session_state.auth_view = "login"
		st.session_state.verification_delivery_notice = ""
		st.rerun()


def render_profile_panel() -> None:
	current_user = st.session_state.current_user
	if current_user is None:
		st.info("Log in or create an account to manage your profile.")
		return

	if st.button("Open API linker", key="open_api_linker", use_container_width=True):
		st.session_state.pending_settings_panel = "Connection"
		st.rerun()

	with st.form("profile_form", clear_on_submit=False):
		display_name = st.text_input("Display name", value=current_user["display_name"])
		st.text_input("Email", value=current_user.get("email", ""), disabled=True)
		bio = st.text_area("Bio", value=current_user.get("bio", ""), height=110)
		if st.form_submit_button("Save Profile", use_container_width=True):
			try:
				updated_user = update_profile(current_user["id"], display_name, bio)
			except ValueError as exc:
				st.error(str(exc))
			else:
				st.session_state.current_user = updated_user
				st.session_state.sidebar_notice = "Profile saved successfully."
				st.rerun()


def build_chat_completions_url(base_url: str) -> str:
	normalized = base_url.strip().rstrip("/")
	if normalized.endswith("/chat/completions"):
		return normalized
	if normalized.endswith("/v1"):
		return f"{normalized}/chat/completions"
	return f"{normalized}/chat/completions"


def build_headers(api_key: str) -> dict[str, str]:
	headers = {
		"Content-Type": "application/json",
		"Accept": "application/json",
	}
	if api_key:
		headers["Authorization"] = f"Bearer {api_key}"
	return headers


def stream_chat_completion(
	url: str,
	headers: dict[str, str],
	payload: dict[str, Any],
	timeout_seconds: int,
):
	response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds, stream=True)
	response.raise_for_status()

	for raw_line in response.iter_lines(decode_unicode=True):
		if not raw_line:
			continue
		if not raw_line.startswith("data:"):
			continue

		data = raw_line.removeprefix("data:").strip()
		if data == "[DONE]":
			break

		parsed = json.loads(data)
		choices = parsed.get("choices", [])
		if not choices:
			continue

		delta = choices[0].get("delta", {})
		content = delta.get("content")
		if content:
			yield content


def get_non_stream_response(
	url: str,
	headers: dict[str, str],
	payload: dict[str, Any],
	timeout_seconds: int,
) -> str:
	response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
	response.raise_for_status()
	data = response.json()
	return data["choices"][0]["message"]["content"]

initialize_database()
initialize_state()
inject_cyberpunk_theme()

with st.sidebar:
	st.markdown("### Agent.ai")
	if st.session_state.sidebar_notice:
		st.success(st.session_state.sidebar_notice)
		st.session_state.sidebar_notice = ""

	api_key = st.session_state.api_key_value
	base_url = st.session_state.base_url_value
	model = st.session_state.model_value
	system_prompt = st.session_state.system_prompt_value
	temperature = st.session_state.temperature_value
	max_tokens = st.session_state.max_tokens_value
	response_length = st.session_state.response_length_value
	token_saver_mode = st.session_state.token_saver_mode_value
	unlimited_output = st.session_state.unlimited_output_value
	timeout_seconds = st.session_state.timeout_seconds_value
	use_streaming = st.session_state.use_streaming_value

	if st.session_state.current_user is None:
		render_account_controls()
	else:
		if st.session_state.pending_settings_panel:
			st.session_state.settings_panel_value = st.session_state.pending_settings_panel
			st.session_state.pending_settings_panel = ""

		settings_panel = st.selectbox(
			"Settings panel",
			("Profile", "Connection", "Assistant", "Generation"),
			key="settings_panel_value",
			help="Use the dropdown to switch between app settings.",
		)
		st.caption("API linker is in Settings panel > Connection")

		if settings_panel == "Profile":
			render_profile_panel()
		elif settings_panel == "Connection":
			api_key = st.text_input("API key", key="api_key_value", type="password")
			st.caption("Link your API key and the app will detect the model automatically.")

			if st.button("Link API", key="link_api_key_btn", use_container_width=True):
				resolved_base_url, provider_message = infer_base_url_from_api_key(api_key, st.session_state.base_url_value)
				st.session_state.base_url_value = resolved_base_url
				fingerprint = f"{resolved_base_url}|{api_key.strip()}"
				detected_model, detection_message = detect_model_name(resolved_base_url, api_key)
				if detected_model:
					st.session_state.model_value = detected_model
					st.session_state.sidebar_notice = (
						f"{provider_message} {detection_message}".strip() if provider_message else detection_message
					)
					st.session_state.model_detection_fingerprint = fingerprint
				else:
					st.session_state.model_value = ""
					st.session_state.sidebar_notice = (
						f"{provider_message} {detection_message}".strip() if provider_message else detection_message
					)
				st.rerun()

			if st.session_state.model_value:
				st.text_input("Detected model", value=st.session_state.model_value, disabled=True)
		elif settings_panel == "Assistant":
			system_prompt = st.text_area(
				"System prompt",
				value=st.session_state.system_prompt_value,
				height=160,
			)
			persona = st.selectbox(
				"Response style",
				("Balanced", "Technical", "Creative", "Concise"),
			)
			if persona == "Technical":
				system_prompt += " Respond with precise technical detail and implementation clarity."
			elif persona == "Creative":
				system_prompt += " Respond with more imaginative phrasing while staying useful."
			elif persona == "Concise":
				system_prompt += " Keep answers short, direct, and actionable."
			st.session_state.system_prompt_value = system_prompt
		elif settings_panel == "Generation":
			response_length = st.selectbox(
				"Response length",
				("Auto", "Short", "Medium", "Long"),
				index=("Auto", "Short", "Medium", "Long").index(st.session_state.response_length_value),
				help="Controls how detailed responses should be.",
			)
			token_saver_mode = st.toggle(
				"Token saver mode",
				value=st.session_state.token_saver_mode_value,
				help="Reduce token usage by sending shorter context and limiting response length.",
			)
			temperature = st.slider(
				"Temperature",
				min_value=0.0,
				max_value=1.5,
				value=float(st.session_state.temperature_value),
				step=0.1,
			)
			unlimited_output = st.toggle(
				"Unlimited output",
				value=st.session_state.unlimited_output_value,
				help="When enabled, the app does not send a max_tokens limit.",
			)
			if not unlimited_output:
				max_tokens = st.slider(
					"Max tokens",
					min_value=16,
					max_value=4096,
					value=int(st.session_state.max_tokens_value),
					step=64,
				)
			timeout_seconds = st.slider(
				"Timeout (seconds)",
				min_value=15,
				max_value=180,
				value=int(st.session_state.timeout_seconds_value),
				step=5,
			)
			use_streaming = st.toggle("Stream response", value=st.session_state.use_streaming_value)

	if st.session_state.current_user is None:
		system_prompt = st.session_state.system_prompt_value
	elif settings_panel != "Assistant":
		system_prompt = st.session_state.system_prompt_value
	else:
		st.session_state.system_prompt_value = system_prompt

	st.session_state.temperature_value = temperature
	st.session_state.max_tokens_value = max_tokens
	st.session_state.response_length_value = response_length
	st.session_state.token_saver_mode_value = token_saver_mode
	st.session_state.unlimited_output_value = unlimited_output
	st.session_state.timeout_seconds_value = timeout_seconds
	st.session_state.use_streaming_value = use_streaming

	st.markdown("---")
	st.caption("Settings unlocked after login")

	if st.button("Clear conversation", use_container_width=True):
		st.session_state.messages = [
			{
				"role": "assistant",
				"content": "Conversation cleared. Ask a new question." if st.session_state.current_user else "Conversation cleared. Log in to start a new session.",
			}
		]
		st.rerun()

render_header(
	model=st.session_state.model_value,
	api_key=st.session_state.api_key_value,
)
if not (st.session_state.current_user is None and st.session_state.auth_view in {"register", "verify"}):
	render_floating_help()

if st.session_state.current_user is None and st.session_state.auth_view in {"register", "verify"}:
	if st.session_state.auth_view == "register":
		render_register_page()
	else:
		render_verify_page()
	st.stop()

for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

chat_disabled = st.session_state.current_user is None
if chat_disabled:
	st.info("Log in or create an account from the sidebar to use Agent.ai.")

prompt = st.chat_input("Ask anything...", disabled=chat_disabled)

if prompt:
	st.session_state.messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
		st.markdown(prompt)

	conversation_messages = [
		{"role": message["role"], "content": message["content"]}
		for message in st.session_state.messages
		if message["role"] in {"user", "assistant"}
	]
	if token_saver_mode:
		# Keep only recent conversation turns to reduce token usage.
		conversation_messages = conversation_messages[-6:]

	effective_response_length = resolve_response_length_mode(response_length, prompt)

	length_guidance_map = {
		"Short": "Respond briefly in about 2-4 sentences.",
		"Medium": "Respond with a medium-length answer in about 6-10 sentences with useful detail.",
		"Long": "Respond with a detailed answer in about 10-16 sentences with clear structure.",
	}
	effective_system_prompt = (
		f"{system_prompt} {length_guidance_map.get(effective_response_length, length_guidance_map['Medium'])}"
	).strip()

	request_messages = [{"role": "system", "content": effective_system_prompt}]
	request_messages.extend(conversation_messages)

	payload = {
		"model": model,
		"messages": request_messages,
		"temperature": temperature,
		"stream": use_streaming,
	}
	if not unlimited_output:
		payload["max_tokens"] = max_tokens
	elif st.session_state.credit_cap_tokens_value > 0:
		payload["max_tokens"] = int(st.session_state.credit_cap_tokens_value)

	if token_saver_mode:
		token_saver_cap_map = {"Short": 96, "Medium": 240, "Long": 320}
		token_saver_cap = token_saver_cap_map.get(effective_response_length, 240)
		if payload.get("max_tokens"):
			payload["max_tokens"] = min(int(payload["max_tokens"]), token_saver_cap)
		else:
			payload["max_tokens"] = token_saver_cap

	reply_text = ""
	url = build_chat_completions_url(base_url)
	headers = build_headers(api_key)

	with st.chat_message("assistant"):
		response_placeholder = st.empty()
		try:
			if use_streaming:
				for chunk in stream_chat_completion(url, headers, payload, timeout_seconds):
					reply_text += chunk
					response_placeholder.markdown(reply_text + "▌")
				reply_text = clean_output_text(reply_text)
				response_placeholder.markdown(reply_text or "No response returned.")
			else:
				reply_text = get_non_stream_response(url, headers, payload, timeout_seconds)
				reply_text = clean_output_text(reply_text)
				response_placeholder.markdown(reply_text)
		except requests.HTTPError as exc:
			status_code = exc.response.status_code if exc.response is not None else None
			error_body = exc.response.text if exc.response is not None else str(exc)
			prompt_limit_info = extract_prompt_token_limits(error_body) if status_code == 402 else None
			affordable_tokens = extract_affordable_tokens(error_body) if status_code == 402 else None

			if prompt_limit_info:
				_, allowed_prompt_tokens = prompt_limit_info
				latest_user_message = next(
					(
						m.get("content", "")
						for m in reversed(payload.get("messages", []))
						if isinstance(m, dict) and m.get("role") == "user"
					),
					"",
				)
				retry_payload = dict(payload)
				retry_payload["messages"] = [
					{"role": "user", "content": clean_output_text(latest_user_message)[:80] or "Answer briefly."}
				]
				retry_payload["max_tokens"] = min(int(retry_payload.get("max_tokens", 64) or 64), 64)
				st.session_state.sidebar_notice = (
					f"Provider prompt-token budget is very low ({allowed_prompt_tokens}). Retrying with minimal context."
				)
				try:
					retry_reply = ""
					if use_streaming:
						for chunk in stream_chat_completion(url, headers, retry_payload, timeout_seconds):
							retry_reply += chunk
						retry_reply = retry_reply or "No response returned."
					else:
						retry_reply = get_non_stream_response(url, headers, retry_payload, timeout_seconds)

					reply_text = clean_output_text(retry_reply)
					response_placeholder.markdown(reply_text)
				except requests.HTTPError:
					reply_text = (
						"Request failed because provider prompt-token limit is too low for this account right now. "
						"Try an even shorter prompt or add credits."
					)
					response_placeholder.error(reply_text)
				except requests.RequestException as retry_exc:
					reply_text = f"Network error after minimal-context retry: {retry_exc}"
					response_placeholder.error(reply_text)
			elif affordable_tokens:
				payload["max_tokens"] = affordable_tokens
				st.session_state.max_tokens_value = affordable_tokens
				st.session_state.credit_cap_tokens_value = affordable_tokens
				st.session_state.sidebar_notice = (
					f"Auto-adjusted max_tokens to {affordable_tokens} due to provider credit limits."
				)
				try:
					retry_reply = ""
					if use_streaming:
						for chunk in stream_chat_completion(url, headers, payload, timeout_seconds):
							retry_reply += chunk
						retry_reply = retry_reply or "No response returned."
					else:
						retry_reply = get_non_stream_response(url, headers, payload, timeout_seconds)

					reply_text = clean_output_text(retry_reply)
					response_placeholder.markdown(reply_text)
				except requests.HTTPError as retry_exc:
					retry_body = retry_exc.response.text if retry_exc.response is not None else str(retry_exc)
					reply_text = (
						f"Request failed after auto-adjusting max_tokens to {affordable_tokens}: {retry_body}"
					)
					response_placeholder.error(reply_text)
				except requests.RequestException as retry_exc:
					reply_text = (
						f"Network error after auto-adjusting max_tokens to {affordable_tokens}: {retry_exc}"
					)
					response_placeholder.error(reply_text)
			else:
				reply_text = f"Request failed: {error_body}"
				response_placeholder.error(reply_text)
		except requests.RequestException as exc:
			reply_text = f"Network error: {exc}"
			response_placeholder.error(reply_text)
		except (KeyError, IndexError, json.JSONDecodeError) as exc:
			reply_text = f"Unexpected response format: {exc}"
			response_placeholder.error(reply_text)

	st.session_state.messages.append({"role": "assistant", "content": reply_text})
