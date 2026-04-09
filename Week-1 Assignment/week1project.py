#requirements
#streamlit

import random
import smtplib
import ssl
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote
from urllib import request

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Registration OTP", layout="centered")
st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Rajdhani:wght@400;500;700&display=swap');

	:root {
		--neon-cyan: #33f0ff;
		--neon-blue: #4f8cff;
		--neon-pink: #ff5ea8;
		--panel-bg: rgba(10, 46, 122, 0.92);
		--panel-border: rgba(70, 140, 255, 0.65);
		--text-main: #ffffff;
		--text-muted: #d3e3ff;
	}

	.stApp {
		background:
			radial-gradient(1200px 600px at 10% 10%, rgba(91, 45, 190, 0.35), transparent 60%),
			radial-gradient(900px 600px at 90% 20%, rgba(0, 170, 255, 0.30), transparent 65%),
			radial-gradient(700px 500px at 50% 100%, rgba(255, 94, 168, 0.18), transparent 70%),
			linear-gradient(130deg, #060913 0%, #0b1024 35%, #111635 100%);
		background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%;
		animation: skyPulse 14s ease-in-out infinite;
		color: var(--text-main);
	}

	[data-testid="stAppViewContainer"] {
		background-image:
			linear-gradient(rgba(120, 160, 255, 0.08) 1px, transparent 1px),
			linear-gradient(90deg, rgba(120, 160, 255, 0.08) 1px, transparent 1px);
		background-size: 48px 48px;
	}

	[data-testid="stHeader"] {
		background: transparent;
	}

	.block-container {
		margin-top: 1rem;
		padding: 1.4rem 1.5rem 1.8rem 1.5rem;
		border: 1px solid var(--panel-border);
		border-radius: 20px;
		background: var(--panel-bg);
		backdrop-filter: blur(8px);
		box-shadow:
			0 0 0 1px rgba(255, 255, 255, 0.03) inset,
			0 10px 35px rgba(8, 14, 32, 0.62),
			0 0 28px rgba(51, 240, 255, 0.18);
	}

	h1, h2, h3 {
		font-family: 'Orbitron', sans-serif !important;
		letter-spacing: 0.8px;
		color: var(--text-main);
		text-shadow: none;
	}

	body, p, label, div, input, textarea, button, span {
		font-family: 'Rajdhani', sans-serif !important;
		letter-spacing: 0.3px;
	}

	/* Restore icon fonts so Streamlit expander arrows render as icons, not text. */
	.material-icons,
	.material-icons-round,
	.material-icons-sharp,
	.material-icons-two-tone,
	.material-symbols-outlined,
	.material-symbols-rounded,
	.material-symbols-sharp,
	.codicon {
		font-family: inherit;
		font-family: 'Material Icons', 'Material Symbols Rounded', 'codicon' !important;
		letter-spacing: normal !important;
	}

	[data-testid="stExpander"] summary {
		align-items: center;
	}

	/* Hide expander arrow/icon while keeping expander text visible and clickable. */
	[data-testid="stExpander"] summary > span:first-child {
		opacity: 0 !important;
	}

	[data-testid="stExpander"] summary p {
		margin: 0;
		line-height: 1.2;
	}

	[data-testid="stMarkdownContainer"] p,
	[data-testid="stMarkdownContainer"] div,
	label {
		color: var(--text-main);
	}

	div[data-baseweb="input"] > div,
	div[data-baseweb="select"] > div,
	div[data-baseweb="textarea"] > div {
		background: rgba(102, 110, 122, 0.95) !important;
		border: 1px solid rgba(78, 86, 98, 0.95) !important;
		box-shadow: 0 0 0 1px rgba(210, 216, 226, 0.20) inset;
	}

	div[data-baseweb="input"] > div:focus-within,
	div[data-baseweb="select"] > div:focus-within,
	div[data-baseweb="textarea"] > div:focus-within {
		border-color: var(--neon-cyan) !important;
		box-shadow: 0 0 0 1px var(--neon-cyan) inset, 0 0 18px rgba(51, 240, 255, 0.38);
	}

	input, textarea {
		color: #000000 !important;
		-webkit-text-fill-color: #000000 !important;
	}

	/* Force black text for select widgets and their rendered values. */
	div[data-baseweb="select"] * {
		color: #000000 !important;
		-webkit-text-fill-color: #000000 !important;
	}

	div[data-baseweb="select"] input {
		color: #000000 !important;
		-webkit-text-fill-color: #000000 !important;
	}

	input::placeholder, textarea::placeholder {
		color: #2f3a4f !important;
	}

	/* Keep agreement text area readable (black text on light background). */
	div[data-testid="stTextArea"] textarea {
		color: #000000 !important;
		-webkit-text-fill-color: #000000 !important;
		background: rgba(240, 245, 255, 0.95) !important;
	}

	.feedback-popup {
		margin-top: 0.8rem;
		padding: 0.9rem 1rem;
		border-radius: 12px;
		border: 1px solid rgba(255, 255, 255, 0.4);
		background: rgba(255, 255, 255, 0.9);
		color: #000000;
	}

	.feedback-popup,
	.feedback-popup * {
		color: #000000 !important;
	}

	button[kind="primary"],
	button[kind="secondary"] {
		border-radius: 11px !important;
		border: 1px solid rgba(12, 56, 150, 0.85) !important;
		background: linear-gradient(120deg, rgba(100, 156, 255, 0.95), rgba(76, 130, 230, 0.95)) !important;
		color: #ffffff !important;
		box-shadow: 0 0 18px rgba(34, 88, 190, 0.30);
		transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
	}

	button[kind="primary"]:hover,
	button[kind="secondary"]:hover {
		transform: translateY(-1px);
		border-color: #86fbff !important;
		box-shadow: 0 0 24px rgba(134, 251, 255, 0.34);
	}

	.scifi-title {
		text-align: center;
		padding: 0.8rem 0 0.4rem 0;
	}

	.scifi-kicker {
		display: inline-block;
		font-family: 'Orbitron', sans-serif;
		font-size: 0.78rem;
		letter-spacing: 1.3px;
		text-transform: uppercase;
		color: #9dd9ff;
		padding: 0.2rem 0.7rem;
		border: 1px solid rgba(115, 205, 255, 0.46);
		border-radius: 999px;
		background: rgba(34, 69, 119, 0.35);
	}

	.scifi-sub {
		text-align: center;
		margin-top: -0.3rem;
		margin-bottom: 0.9rem;
		font-size: 1rem;
		color: #b7d4ff;
		letter-spacing: 0.4px;
	}

	@keyframes skyPulse {
		0% { filter: saturate(1.0) brightness(1.0); }
		50% { filter: saturate(1.12) brightness(1.05); }
		100% { filter: saturate(1.0) brightness(1.0); }
	}
	</style>
	""",
	unsafe_allow_html=True,
)

OTP_VALIDITY_SECONDS = 120
COUNTDOWN_SECONDS = 10
GMAIL_ADDRESS = "hareshgrownup@gmail.com"
GMAIL_APP_PASSWORD = "usrb eapu turb blpy"
LOCATION_DATA = {
	"India": {
		"Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur"],
		"Arunachal Pradesh": ["Itanagar", "Naharlagun", "Tawang"],
		"Assam": ["Guwahati", "Dibrugarh", "Silchar"],
		"Bihar": ["Patna", "Gaya", "Muzaffarpur"],
		"Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur"],
		"Goa": ["Panaji", "Margao", "Vasco da Gama"],
		"Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
		"Haryana": ["Gurugram", "Faridabad", "Panipat"],
		"Himachal Pradesh": ["Shimla", "Dharamshala", "Mandi"],
		"Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad"],
		"Karnataka": ["Bengaluru", "Mysuru", "Mangaluru"],
		"Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode"],
		"Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
		"Maharashtra": ["Mumbai", "Pune", "Nagpur"],
		"Manipur": ["Imphal", "Thoubal", "Churachandpur"],
		"Meghalaya": ["Shillong", "Tura", "Jowai"],
		"Mizoram": ["Aizawl", "Lunglei", "Champhai"],
		"Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
		"Odisha": ["Bhubaneswar", "Cuttack", "Rourkela"],
		"Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
		"Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
		"Sikkim": ["Gangtok", "Namchi", "Gyalshing"],
		"Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
		"Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
		"Tripura": ["Agartala", "Udaipur", "Dharmanagar"],
		"Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
		"Uttarakhand": ["Dehradun", "Haridwar", "Haldwani"],
		"West Bengal": ["Kolkata", "Howrah", "Siliguri"],
		"Andaman and Nicobar Islands": ["Port Blair", "Diglipur", "Car Nicobar"],
		"Chandigarh": ["Chandigarh", "Sector 17", "Manimajra"],
		"Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Diu", "Silvassa"],
		"Delhi": ["New Delhi", "Dwarka", "Rohini"],
		"Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag"],
		"Ladakh": ["Leh", "Kargil", "Diskit"],
		"Lakshadweep": ["Kavaratti", "Agatti", "Amini"],
		"Puducherry": ["Puducherry", "Karaikal", "Mahe"],
	},
	"USA": {
		"California": ["Los Angeles", "San Diego", "San Jose"],
		"Texas": ["Houston", "Dallas", "Austin"],
		"New York": ["New York City", "Buffalo", "Albany"],
	},
	"Canada": {
		"Ontario": ["Toronto", "Ottawa", "Hamilton"],
		"British Columbia": ["Vancouver", "Victoria", "Kelowna"],
		"Quebec": ["Montreal", "Quebec City", "Laval"],
	},
}

COUNTRIES_NOW_BASE_URL = "https://countriesnow.space/api/v0.1/countries"
REST_COUNTRIES_BASE_URL = "https://restcountries.com/v3.1/name"
CAPTCHA_WORDS = ["RIVER", "MANGO", "TIGER", "PLANET", "ORANGE", "PYTHON"]
MANDATORY_YOUTUBE_URL = "https://www.youtube.com/watch?v=ZQ75bgoyQ1M&list=RDZQ75bgoyQ1M&start_radio=1"
CAPTCHA_KNOWLEDGE_OPTIONS = [
	"Select answer",
	"O(V^2)",
	"O((V + E) log V)",
	"O(E^2)",
	"O(log V)",
]
TERMS_CONFIRM_PHRASE = "I HAVE READ EVERY CLAUSE OF THE QUANTUM IDENTITY AGREEMENT"
INTRO_CONDITIONS = [
	"This is a demo project for learning and portfolio demonstration only.",
	"You cannot copy, redistribute, or claim this project as your own work.",
	"This project is built using Streamlit with help from GitHub Copilot.",
]
TERMS_AND_CONDITIONS_TEXT = f"""
QUANTUM IDENTITY REGISTRATION AGREEMENT (QIRA)
Version 1.0 | Effective Date: 2026-04-06

Please read this full agreement carefully. By continuing, you acknowledge that you understand and accept every clause below.

1. Purpose of Registration
1.1 This registration flow exists to validate identity contact pathways and prevent unauthorized access.
1.2 The platform may request strict input quality checks to reduce spam, fraud, and synthetic submissions.

2. User Data Responsibility
2.1 You confirm that all mandatory fields are accurate to the best of your knowledge.
2.2 You agree not to provide intentionally false, generated, spoofed, or misleading personal details.
2.3 You understand that validation errors may block progression until corrected.

3. Verification Workflow Consent
3.1 You consent to multi-step verification, including CAPTCHA challenges and one-time-password (OTP) checks.
3.2 You accept that challenge difficulty may increase for unusual or suspicious submission patterns.
3.3 You acknowledge that successful challenge completion does not guarantee account approval; it only allows workflow progression.

4. OTP and Communication Terms
4.1 OTP delivery depends on external email infrastructure and may be delayed by network conditions.
4.2 OTP codes are time-bound and must not be shared with third parties.
4.3 Repeated failed OTP attempts may trigger temporary lockouts.

5. Security and Abuse Policy
5.1 Automated attacks, scripted attempts, token replay, and brute-force behavior are prohibited.
5.2 The system may throttle, reject, or log abusive requests for defense and audit purposes.
5.3 You agree that deliberate abuse attempts may result in permanent denial of service for your session.

6. Geographic and Contact Metadata
6.1 Country, state, city, and phone code selections are provided for structured data consistency.
6.2 Data mappings may depend on third-party geographic services and can vary over time.
6.3 Postal/ZIP rules may differ by region; your submission must still satisfy mandatory system validation.

7. User Interface and Waiting Period
7.1 The platform may impose waiting periods before allowing irreversible actions.
7.2 The waiting period exists to reduce accidental acceptance and ensure informed consent.
7.3 Attempting to proceed before timer completion may result in warnings requiring additional confirmation.

8. Accuracy and Originality Requirements
8.1 You confirm your entries are personally provided and not copied from arbitrary filler text.
8.2 Placeholder values such as random strings, repeated characters, or meaningless test values are not permitted for mandatory fields.
8.3 The platform reserves the right to reject low-quality submissions that fail authenticity heuristics.

9. Limitation and Availability
9.1 Service availability is not guaranteed and may be interrupted by maintenance, dependency outages, or security updates.
9.2 Feature behavior may evolve without prior notice to improve trust and safety.
9.3 This workflow is provided as-is for secure registration purposes.

10. Final Acceptance
10.1 By clicking the agree button after the waiting period, you affirm you have read this entire agreement.
10.2 You acknowledge this action is intentional and informed.
10.3 You accept all workflow checks, restrictions, and verification steps required by this system.

CONFIRMATION SENTENCE (type exactly in the field below):
{TERMS_CONFIRM_PHRASE}
"""



def post_json(url: str, payload: dict) -> dict:
	data = json.dumps(payload).encode("utf-8")
	req = request.Request(
		url,
		data=data,
		headers={"Content-Type": "application/json"},
		method="POST",
	)
	with request.urlopen(req, timeout=8) as response:
		return json.loads(response.read().decode("utf-8"))


@st.cache_data(ttl=60 * 60)
def fetch_all_countries() -> list[str]:
	try:
		with request.urlopen(f"{COUNTRIES_NOW_BASE_URL}/positions", timeout=8) as response:
			payload = json.loads(response.read().decode("utf-8"))
		countries = sorted({item.get("name", "").strip() for item in payload.get("data", []) if item.get("name")})
		if countries:
			return countries
	except Exception:
		pass
	return sorted(LOCATION_DATA.keys())


@st.cache_data(ttl=60 * 60)
def fetch_states(country: str) -> list[str]:
	if not country:
		return ["N/A"]

	try:
		payload = post_json(f"{COUNTRIES_NOW_BASE_URL}/states", {"country": country})
		states = payload.get("data", {}).get("states", [])
		state_names = [state.get("name", "").strip() for state in states if state.get("name")]
		if state_names:
			return state_names
	except Exception:
		pass

	if country in LOCATION_DATA:
		return list(LOCATION_DATA[country].keys())

	return ["N/A"]


@st.cache_data(ttl=60 * 60)
def fetch_cities(country: str, state: str) -> list[str]:
	if not country:
		return ["N/A"]

	if state and state != "N/A":
		try:
			payload = post_json(
				f"{COUNTRIES_NOW_BASE_URL}/state/cities",
				{"country": country, "state": state},
			)
			cities = [city.strip() for city in payload.get("data", []) if isinstance(city, str) and city.strip()]
			if cities:
				return cities
		except Exception:
			pass

	if country in LOCATION_DATA and state in LOCATION_DATA[country]:
		return LOCATION_DATA[country][state]

	return ["N/A"]


def is_valid_email(email: str) -> bool:
	import re
	return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def has_any_digit(value: str) -> bool:
	return any(ch.isdigit() for ch in value)


def is_valid_name(name: str) -> bool:
	import re
	return bool(re.fullmatch(r"[A-Za-z][A-Za-z\s'-]*", name))


def is_original_text(value: str) -> bool:
	cleaned = value.strip().lower()
	blocked = {"test", "abc", "qwerty", "asdf", "none", "null", "na", "xxx", "unknown"}
	if cleaned in blocked:
		return False
	if len(set(cleaned.replace(" ", ""))) <= 1 and len(cleaned.replace(" ", "")) >= 3:
		return False
	return True


def is_valid_phone_number(value: str) -> bool:
	digits = value.strip()
	return digits.isdigit() and 6 <= len(digits) <= 15


@st.cache_data(ttl=60 * 60 * 24)
def fetch_country_phone_code(country: str) -> str:
	if not country:
		return "N/A"

	for full_text in ("true", "false"):
		try:
			url = f"{REST_COUNTRIES_BASE_URL}/{quote(country)}?fullText={full_text}&fields=name,idd"
			with request.urlopen(url, timeout=8) as response:
				payload = json.loads(response.read().decode("utf-8"))

			if isinstance(payload, list) and payload:
				for item in payload:
					name_data = item.get("name", {})
					common = name_data.get("common", "")
					official = name_data.get("official", "")
					if country.lower() not in {str(common).lower(), str(official).lower()} and full_text == "true":
						continue

					idd = item.get("idd", {})
					root = idd.get("root", "")
					suffixes = idd.get("suffixes", [])
					if root and suffixes:
						return f"{root}{suffixes[0]}"
					if root:
						return root
		except Exception:
			continue

	fallback_codes = {
		"India": "+91",
		"USA": "+1",
		"United States": "+1",
		"Canada": "+1",
		"United Kingdom": "+44",
		"Australia": "+61",
	}
	return fallback_codes.get(country, "N/A")


def reset_captcha_challenge() -> None:
	st.session_state.captcha_word = random.choice(CAPTCHA_WORDS)
	st.session_state.captcha_a = random.randint(2, 20)
	st.session_state.captcha_b = random.randint(2, 20)


def verify_captcha_inputs(word_input: str, math_input: str, knowledge_answer: str) -> tuple[bool, str]:
	expected_word = st.session_state.get("captcha_word", "")
	expected_sum = st.session_state.get("captcha_a", 0) + st.session_state.get("captcha_b", 0)

	if word_input.strip().upper() != expected_word:
		return False, "CAPTCHA word does not match."
	if not math_input.strip().isdigit() or int(math_input.strip()) != expected_sum:
		return False, "CAPTCHA math answer is incorrect."
	if knowledge_answer != "O((V + E) log V)":
		return False, "Complex knowledge check failed. Please review and answer correctly."
	return True, ""


def apply_window_guard(require_feedback: bool) -> None:
	flag = "true" if require_feedback else "false"
	components.html(
		f"""
		<script>
		(function () {{
			const hostWindow = window.parent || window;
			hostWindow.__mustCompleteFeedback = {flag};

			hostWindow.onbeforeunload = function (event) {{
				if (!hostWindow.__mustCompleteFeedback) return;
				const msg = 'Please complete final feedback before leaving this page.';
				event.preventDefault();
				event.returnValue = msg;
				return msg;
			}};
		}})();
		</script>
		""",
		height=0,
	)


def show_fullscreen_mode_button() -> None:
	components.html(
		"""
		<div style='margin-top:8px;'>
			<button id='fs-lock-btn' style='width:100%; padding:10px 12px; border-radius:10px; border:1px solid #4f8cff; background:#183a7a; color:#fff; cursor:pointer;'>
				Enable Fullscreen Lock Mode
			</button>
		</div>
		<script>
		(function () {
			const btn = document.getElementById('fs-lock-btn');
			if (!btn) return;
			btn.addEventListener('click', async () => {
				try {
					const root = window.parent.document.documentElement;
					if (!window.parent.document.fullscreenElement) {
						await root.requestFullscreen();
					}
				} catch (e) {
					console.log('Fullscreen request blocked by browser:', e);
				}
			});
		})();
		</script>
		""",
		height=64,
	)


def send_otp_email(to_email: str, otp: str) -> tuple[bool, str]:
	gmail_address = GMAIL_ADDRESS
	gmail_app_password = GMAIL_APP_PASSWORD

	if not gmail_address or not gmail_app_password:
		return False, "Gmail credentials are missing in the source code."

	msg = MIMEMultipart("alternative")
	msg["Subject"] = "Your OTP Code"
	msg["From"] = gmail_address
	msg["To"] = to_email

	body = (
		f"Hello,\n\n"
		f"Your One-Time Password (OTP) is: {otp}\n\n"
		f"It is valid for {OTP_VALIDITY_SECONDS} seconds.\n\n"
		f"If you did not request this, please ignore this email."
	)
	msg.attach(MIMEText(body, "plain"))

	try:
		context = ssl.create_default_context()
		with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
			server.login(gmail_address, gmail_app_password)
			server.sendmail(gmail_address, to_email, msg.as_string())
		return True, "OTP sent successfully."
	except Exception as exc:
		return False, f"Failed to send email: {exc}"


def reset_state() -> None:
	for key in ["step", "first_name", "last_name", "email", "phone",
				"phone_code", "full_phone", "address_line_1", "address_line_2", "zipcode", "country", "state", "city",
				"pending_registration", "terms_started_at", "captcha_word", "captcha_a", "captcha_b",
				"feedback_emoji", "feedback_submitted",
				"otp", "otp_created_at", "countdown_start", "error"]:
		st.session_state.pop(key, None)


if "step" not in st.session_state:
	st.session_state.step = "intro_1"
	st.session_state.error = ""

if st.session_state.get("step") == "form" and not st.session_state.get("intro_completed", False):
	st.session_state.step = "intro_1"


st.markdown(
	"""
	<div class='scifi-title'>
		<div class='scifi-kicker'>Identity Verification Node</div>
		<h1>Registration Form</h1>
	</div>
	<div class='scifi-sub'>Enter authentic details to proceed through the secure gateway.</div>
	""",
	unsafe_allow_html=True,
)

# ── STEP 1: Fill the form ─────────────────────────────────────────────────────
if st.session_state.step == "intro_1":
	st.markdown("<h3 style='color:#000000;'>Startup Agreement 1/3</h3>", unsafe_allow_html=True)
	st.markdown("<div class='feedback-popup'><strong>Condition 1:</strong><br/>" + INTRO_CONDITIONS[0] + "</div>", unsafe_allow_html=True)
	if st.button("I Agree - Continue to Condition 2"):
		st.session_state.step = "intro_2"
		st.rerun()

elif st.session_state.step == "intro_2":
	st.markdown("<h3 style='color:#000000;'>Startup Agreement 2/3</h3>", unsafe_allow_html=True)
	st.markdown("<div class='feedback-popup'><strong>Condition 2:</strong><br/>" + INTRO_CONDITIONS[1] + "</div>", unsafe_allow_html=True)
	col_prev, col_next = st.columns(2)
	with col_prev:
		if st.button("Back"):
			st.session_state.step = "intro_1"
			st.rerun()
	with col_next:
		if st.button("I Agree - Continue to Condition 3"):
			st.session_state.step = "intro_3"
			st.rerun()

elif st.session_state.step == "intro_3":
	st.markdown("<h3 style='color:#000000;'>Startup Agreement 3/3</h3>", unsafe_allow_html=True)
	st.markdown("<div class='feedback-popup'><strong>Condition 3:</strong><br/>" + INTRO_CONDITIONS[2] + "</div>", unsafe_allow_html=True)
	col_prev, col_start = st.columns(2)
	with col_prev:
		if st.button("Back"):
			st.session_state.step = "intro_2"
			st.rerun()
	with col_start:
		if st.button("I Agree - Start Form"):
			st.session_state.intro_completed = True
			st.session_state.step = "form"
			st.rerun()

elif st.session_state.step == "form":
	st.subheader("Please fill in your details")
	first_name = st.text_input("First Name 🔴")
	last_name  = st.text_input("Last Name")
	email      = st.text_input("Email Address 🔴")

	col_addr1, col_addr2 = st.columns(2)
	with col_addr1:
		address_line_1 = st.text_input("Address Line 1 🔴", max_chars=30)
	with col_addr2:
		address_line_2 = st.text_input("Address Line 2", max_chars=30)

	country_options = fetch_all_countries()
	country = st.selectbox("Country 🔴", options=country_options)

	state_options = fetch_states(country)
	state = st.selectbox("State 🔴", options=state_options)

	city_options = fetch_cities(country, state)
	city = st.selectbox("City 🔴", options=city_options)
	zipcode = st.text_input("ZIP / Postal Code 🔴", max_chars=10)

	phone_code = fetch_country_phone_code(country)
	col_code, col_phone = st.columns([1, 3])
	with col_code:
		st.text_input("Code", value=phone_code, disabled=True)
	with col_phone:
		phone = st.text_input("Phone Number 🔴")

	submit = st.button("Submit")

	if submit:
		errors = []
		warnings = []
		if not first_name.strip():
			errors.append("First name is required.")
		elif has_any_digit(first_name):
			warnings.append("First name should not contain numbers.")
			errors.append("Enter a valid first name (letters only).")
		elif not is_valid_name(first_name.strip()):
			errors.append("Enter a valid first name (letters only).")
		elif len(first_name.strip()) < 2 or not is_original_text(first_name):
			errors.append("First name must look original and contain at least 2 letters.")

		if last_name.strip():
			if has_any_digit(last_name):
				warnings.append("Last name should not contain numbers.")
				errors.append("Enter a valid last name (letters only).")
			elif not is_valid_name(last_name.strip()):
				errors.append("Enter a valid last name (letters only).")
			elif len(last_name.strip()) < 2 or not is_original_text(last_name):
				errors.append("Last name must look original and contain at least 2 letters.")

		if not is_valid_email(email.strip()):
			errors.append("Enter a valid email address.")
		if not phone.strip():
			errors.append("Phone number is required.")
		elif any(ch.isalpha() for ch in phone):
			warnings.append("Phone number should not contain words.")
			errors.append("Enter a valid phone number with digits only.")
		elif not is_valid_phone_number(phone):
			errors.append("Phone number must contain only digits and be 6 to 15 digits long.")
		if not address_line_1.strip():
			errors.append("Address Line 1 is required.")
		elif len(address_line_1.strip()) < 5 or not is_original_text(address_line_1):
			errors.append("Address Line 1 should be meaningful and at least 5 characters.")
		if not zipcode.strip():
			errors.append("ZIP / Postal Code is required.")
		elif any(ch.isalpha() for ch in zipcode):
			warnings.append("ZIP / Postal Code should not contain words.")
			errors.append("Enter a valid ZIP / Postal Code with digits only.")
		elif not zipcode.strip().isdigit() or not (3 <= len(zipcode.strip()) <= 10):
			errors.append("ZIP / Postal Code must be 3 to 10 digits.")

		if warnings:
			for warning in warnings:
				st.warning(warning)

		if errors:
			st.session_state.error = "\n".join(errors)
		else:
			st.session_state.pending_registration = {
				"first_name": first_name.strip(),
				"last_name": last_name.strip(),
				"email": email.strip(),
				"phone": phone.strip(),
				"phone_code": phone_code,
				"full_phone": f"{phone_code} {phone.strip()}" if phone_code != "N/A" else phone.strip(),
				"address_line_1": address_line_1.strip(),
				"address_line_2": address_line_2.strip(),
				"zipcode": zipcode.strip(),
				"country": country,
				"state": state,
				"city": city,
			}
			st.session_state.error = ""
			st.session_state.step = "captcha"
			st.rerun()

	if st.session_state.error:
		st.error(st.session_state.error)


# ── STEP 1.5: reCAPTCHA ──────────────────────────────────────────────────────
elif st.session_state.step == "captcha":
	st.subheader("Security Check")
	st.write("Please complete this CAPTCHA check before we send your OTP.")

	if "captcha_word" not in st.session_state or "captcha_a" not in st.session_state or "captcha_b" not in st.session_state:
		reset_captcha_challenge()

	st.info(f"Type this word exactly: {st.session_state.captcha_word}")
	entered_word = st.text_input("CAPTCHA Word")
	entered_math = st.text_input(f"What is {st.session_state.captcha_a} + {st.session_state.captcha_b}?")
	knowledge_answer = st.selectbox(
		"Knowledge Check: For Dijkstra's algorithm with adjacency list and binary heap, what is the time complexity?",
		options=CAPTCHA_KNOWLEDGE_OPTIONS,
	)
	confirm_human = st.checkbox("I confirm I am not a robot")

	col1, col2 = st.columns(2)
	with col1:
		if st.button("Continue to Verification"):
			if not confirm_human:
				st.session_state.error = "Please confirm you are not a robot."
				st.rerun()

			is_human, captcha_msg = verify_captcha_inputs(entered_word, entered_math, knowledge_answer)
			if not is_human:
				st.session_state.error = captcha_msg
				reset_captcha_challenge()
			else:
				pending = st.session_state.get("pending_registration")
				if not pending:
					st.session_state.error = "Registration data expired. Please fill the form again."
					st.session_state.step = "form"
					st.rerun()
				st.session_state.error = ""
				st.session_state.terms_started_at = time.time()
				st.session_state.step = "terms"
				st.rerun()

	with col2:
		if st.button("Back to Form"):
			reset_captcha_challenge()
			st.session_state.step = "form"
			st.rerun()

	if st.session_state.error:
		st.error(st.session_state.error)


# ── STEP 1.75: Terms & Conditions ───────────────────────────────────────────
elif st.session_state.step == "terms":
	st.subheader("User Agreement and Terms")
	st.write("Read the full agreement below. You must complete the wait timer and confirm the sentence to continue. The video is optional.")

	if "terms_started_at" not in st.session_state:
		st.session_state.terms_started_at = time.time()

	st.text_area(
		"Terms and Conditions (Complete Text)",
		value=TERMS_AND_CONDITIONS_TEXT,
		height=360,
		disabled=True,
	)

	st.markdown("### Optional Video While You Wait")
	st.write("Open this link in YouTube during the 30-second waiting period:")
	st.markdown(f"[Go to YouTube]({MANDATORY_YOUTUBE_URL})")

	confirmation_input = st.text_input("Type the confirmation sentence exactly")
	elapsed = time.time() - st.session_state.terms_started_at
	remaining = max(0, 30 - int(elapsed))

	col_agree, col_back = st.columns(2)
	with col_agree:
		agree = st.button("I Agree and Continue")
	with col_back:
		go_back = st.button("Back")

	st.caption(f"Wait timer: {remaining} seconds remaining. Use this time to read terms (video is optional).")

	if agree:
		if confirmation_input.strip() != TERMS_CONFIRM_PHRASE:
			st.session_state.error = "Please read fully and type the confirmation sentence exactly before continuing."
		elif remaining > 0:
			st.session_state.error = "Please wait for 30 seconds or read the terms fully before continuing."
		else:
			pending = st.session_state.get("pending_registration")
			if not pending:
				st.session_state.error = "Registration data expired. Please fill the form again."
				st.session_state.step = "form"
				st.rerun()

			new_otp = f"{random.randint(0, 999999):06d}"
			sent, msg = send_otp_email(pending["email"], new_otp)
			if sent:
				st.session_state.first_name = pending["first_name"]
				st.session_state.last_name = pending["last_name"]
				st.session_state.email = pending["email"]
				st.session_state.phone = pending["phone"]
				st.session_state.phone_code = pending["phone_code"]
				st.session_state.full_phone = pending["full_phone"]
				st.session_state.address_line_1 = pending["address_line_1"]
				st.session_state.address_line_2 = pending["address_line_2"]
				st.session_state.zipcode = pending["zipcode"]
				st.session_state.country = pending["country"]
				st.session_state.state = pending["state"]
				st.session_state.city = pending["city"]
				st.session_state.otp = new_otp
				st.session_state.otp_created_at = time.time()
				st.session_state.pending_registration = None
				st.session_state.error = ""
				st.session_state.step = "verify"
				st.rerun()
			else:
				st.session_state.error = msg

	if go_back:
		st.session_state.step = "captcha"
		st.session_state.error = ""
		st.rerun()

	if st.session_state.error:
		st.error(st.session_state.error)


# ── STEP 2: Verify OTP ────────────────────────────────────────────────────────
elif st.session_state.step == "verify":
	st.subheader("Verify Your Email")
	st.write(f"An OTP has been sent to **{st.session_state.email}**")

	remaining = max(0, OTP_VALIDITY_SECONDS - int(time.time() - st.session_state.otp_created_at))
	st.caption(f"OTP expires in {remaining} seconds")

	with st.form("otp_form"):
		entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6)
		verify = st.form_submit_button("Verify OTP")

	col1, col2 = st.columns(2)
	with col1:
		if st.button("Resend OTP"):
			new_otp = f"{random.randint(0, 999999):06d}"
			sent, msg = send_otp_email(st.session_state.email, new_otp)
			if sent:
				st.session_state.otp            = new_otp
				st.session_state.otp_created_at = time.time()
				st.session_state.error          = ""
				st.success("OTP resent successfully.")
			else:
				st.session_state.error = msg
	with col2:
		if st.button("Cancel"):
			reset_state()
			st.rerun()

	if verify:
		if remaining <= 0:
			st.session_state.error = "OTP expired. Please resend."
		elif entered_otp.strip() == st.session_state.otp:
			st.session_state.error          = ""
			st.session_state.step           = "done"
			st.session_state.countdown_start = time.time()
			st.rerun()
		else:
			st.session_state.error = "Incorrect OTP. Please try again."

	if st.session_state.error:
		st.error(st.session_state.error)


# ── STEP 3: Success + countdown ──────────────────────────────────────────────
elif st.session_state.step == "done":
	apply_window_guard(require_feedback=True)
	st.success("Verification was successful!")
	st.markdown("---")

	elapsed   = time.time() - st.session_state.countdown_start
	remaining = max(0, COUNTDOWN_SECONDS - int(elapsed))

	st.markdown(
		"<h2 style='text-align:center; color:#e74c3c;'>TESTING ENDING</h2>",
		unsafe_allow_html=True,
	)
	countdown_placeholder = st.empty()
	countdown_placeholder.markdown(
		f"<h3 style='text-align:center;'>Closing in {remaining} second{'s' if remaining != 1 else ''}...</h3>",
		unsafe_allow_html=True,
	)

	if remaining > 0:
		time.sleep(1)
		st.rerun()
	else:
		countdown_placeholder.markdown(
			"<h3 style='text-align:center; color:grey;'>Session ended.</h3>",
			unsafe_allow_html=True,
		)
		st.markdown("<div class='feedback-popup'><strong>Final Checkpoint Popup</strong><br/>The 10-second countdown is complete. Please submit feedback before closing the session.</div>", unsafe_allow_html=True)
		show_fullscreen_mode_button()
		emoji_options = ["🤩", "😊", "😐", "😕", "😡"]
		default_emoji = st.session_state.get("feedback_emoji", "😊")
		if default_emoji not in emoji_options:
			default_emoji = "😊"

		selected_emoji = st.radio(
			"Pick an emoji for your experience",
			options=emoji_options,
			horizontal=True,
			index=emoji_options.index(default_emoji),
		)

		nonsense_q1 = st.selectbox(
			"If your keyboard were a planet, what would its weather be?",
			options=["Cosmic rain", "Pixel storm", "Neon sunshine", "Meteor drizzle"],
		)
		nonsense_q2 = st.radio(
			"Which snack gives better coding power?",
			options=["Invisible chips", "Quantum samosa", "Anti-gravity popcorn", "Binary biscuit"],
			horizontal=True,
		)

		if st.button("Submit and Close Session"):
			st.session_state.feedback_emoji = selected_emoji
			st.session_state.feedback_submitted = True
			st.session_state.step = "closed"
			st.rerun()


elif st.session_state.step == "closed":
	apply_window_guard(require_feedback=False)
	st.success("Session closed successfully.")
	if st.session_state.get("feedback_submitted"):
		emoji = st.session_state.get("feedback_emoji", "😊")
		st.info(f"Feedback saved: {emoji}")
	st.write("Thanks for completing the final questions.")

st.markdown("---")
st.markdown(
	"""
	<div style='text-align:center; color:#888; font-size:13px; padding:10px 0 4px 0;'>
		Built with ❤️ using
		<a href='https://streamlit.io' target='_blank' style='color:#FF4B4B; text-decoration:none;'>Streamlit</a>
		&nbsp;·&nbsp; © 2026 Registration OTP Demo
	</div>
	<div style='text-align:center; padding:6px 0 10px 0;'>
		<a href='https://www.instagram.com/stellar_pulse_interactive' target='_blank'
		   style='text-decoration:none; margin:0 10px; display:inline-flex; align-items:center; gap:6px;' title='Instagram'>
			<img src='https://cdn.simpleicons.org/instagram/E4405F' alt='Instagram' width='22' height='22' style='vertical-align:middle;' />
			<span style='font-size:16px; color:#E4405F;'>Instagram</span>
		</a>
		<a href='https://www.youtube.com/@SPulseInteractiveEntertainment' target='_blank'
		   style='text-decoration:none; margin:0 10px; display:inline-flex; align-items:center; gap:6px;' title='YouTube'>
			<img src='https://cdn.simpleicons.org/youtube/FF0000' alt='YouTube' width='22' height='22' style='vertical-align:middle;' />
			<span style='font-size:16px; color:#FF0000;'>YouTube</span>
		</a>
	</div>
	""",
	unsafe_allow_html=True,
)
