import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import openai, silero


# ============================================================
# LOAD .ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("\n========== ENV CHECK ==========")
print("LIVEKIT_URL:", LIVEKIT_URL)
print("LIVEKIT_API_KEY:", LIVEKIT_API_KEY)
print("LIVEKIT_API_SECRET:", "SET" if LIVEKIT_API_SECRET else "MISSING")
print("OPENAI_API_KEY:", "SET" if OPENAI_API_KEY else "MISSING")
print("================================\n")

if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET or not OPENAI_API_KEY:
    raise RuntimeError("Missing env variables. Check your .env file.")


# ============================================================
# AGENT CLASS
# ============================================================

class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are an English-only AI voice assistant.

STRICT RULES:
- Always speak English only.
- Never speak Tamil, Hindi, Spanish, French, or any other language.
- Keep replies short, clear, and natural.
- If the user says hello, hi, or hey, reply: "Hello! How can I help you?"
- Never say "you're welcome" unless the user clearly says "thank you".
- Never say "goodbye" unless the user clearly says bye, goodbye, see you, or asks to end.
- If the input is unclear, ask: "Could you repeat that?"
"""
        )


# ============================================================
# ENTRYPOINT
# ============================================================

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        # Voice Activity Detection for mic input
        vad=silero.VAD.load(
            min_speech_duration=0.2,
            min_silence_duration=0.8,
            activation_threshold=0.3,
        ),

        # Speech to Text
        stt=openai.STT(
            model="whisper-1",
            language="en",
        ),

        # LLM
        llm=openai.responses.LLM(
            model="gpt-4.1-mini",
        ),

        # Text to Speech
        tts=openai.TTS(
            model="gpt-4o-mini-tts",
            voice="ash",
            instructions="""
Speak only in English.
Use a clear natural English voice.
Keep replies short.
Do not say goodbye unless the user says goodbye.
""",
        ),
    )

    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    # ------------------------------------------------------------
    # TEXT INPUT FROM BROWSER DATA MESSAGE
    # ------------------------------------------------------------
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        try:
            message = data_packet.data.decode("utf-8").strip()

            print("\n==============================")
            print("TEXT INPUT FROM WEB:", message)
            print("==============================\n")

            if not message:
                return

            asyncio.create_task(
                session.generate_reply(
                    instructions=f"""
The user typed this message:
{message}

Reply to the user in English only.
If the message is a greeting like hello, hi, or hey, say exactly:
Hello! How can I help you?
"""
                )
            )

        except Exception as e:
            print("Data message error:", e)

    # Initial greeting
    await session.generate_reply(
        instructions="Say exactly: Hello! I am ready. You can type a message or turn on the microphone."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )