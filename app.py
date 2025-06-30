import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import requests
from datetime import datetime
from langdetect import detect
import os

# Load environment variables
load_dotenv()

# Page setup
st.set_page_config(page_title="Radiology Simplifier", page_icon="🧾", layout="centered")

#Styling
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        .stTextArea textarea {
            font-size: 16px;
            line-height: 1.6;
            padding: 1em;
        }
        .stButton > button {
            border-radius: 12px;
            padding: 0.6em 1.4em;
            font-size: 16px;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Your system prompt exactly as given
system_prompt = """
You are a compassionate, clear-speaking doctor explaining radiology results to a patient.
Rewrite the following radiology report in language that is simple, respectful, and easy to understand.
Speak the way an ideal doctor would — someone who is calm, kind, knowledgeable, and emotionally intelligent.
Your explanation should:
•   Be written at a 7th–8th grade reading level
•   Avoid unnecessary medical jargon; explain any technical terms briefly if needed
•   Be accurate and clinically responsible — don’t overstate or speculate
•   Reassure the patient when appropriate, without minimizing serious findings
•   Offer helpful context and clearly mention any next steps or recommendations in the report
Structure your output like this:
1.  A short summary of the most important points in one sentence -> if the patient only has time to read this one sentence, he/she should be able to get as much information out of this one sentence as possible
2.  What was found (in plain language)
3.  What it might mean (calm, non-alarming tone)
4.  What happens next (based on what the report says)
Use this at the beginning of the sections as a title:
    1: "💬 One-sentence Summary",
    2: "🔍 What Was Found",
    3: "🧠 What It Might Mean",
    4: "📋 What Happens Next"
Style:
•   Make the complex radiology report seem simple after the simplification
•   Break the complex report down into simpler pieces the patient can understand
•   Don’t invent things that are not mentioned in the report
•   Write it like the patient would explain it to someone else who has no medical background
Here is the report to simplify:
"""

# Session usage tracking
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

# Title and description
st.title("🧾 Radiology Report Simplifier")
st.caption("Understand your radiology report in clear, kind language.")

#st.markdown("Build by a Medical Student. Build to save time and frustration" )

# Legal disclaimer
st.markdown("""
> ⚠️ _This tool is for informational purposes only and not a substitute for professional medical advice.  
No data is stored. Always consult your healthcare provider._
""")

# Input section
report_input = st.text_area("📄 Paste your radiology report below", height=300, placeholder="Type or paste your radiology report here...")

# Button and processing
if st.button("✨ Simplify Report"):
    if not report_input.strip():
        st.warning("Please paste a report first.")
    elif st.session_state.usage_count >= 3:
        st.warning("You've reached the limit of 3 uses for this session. Please refresh or restart to continue.")
    else:
        with st.spinner("Analyzing and simplifying your report..."):
            try:

                # detect language
                try:
                    detected_lang = detect(report_input.strip())
                    st.session_state.language = detected_lang
                except:
                    detected_lang = "en"

                # Language instruction map
                lang_instruction = {
                    "en": "Please write the explanation in English.",
                    "de": "Bitte schreibe die Erklärung auf Deutsch.",
                    "fr": "Veuillez rédiger l'explication en français.",                        "es": "Por favor, escriba la explicación en español.",
                    "it": "Per favore, scrivi la spiegazione in italiano.",
                }.get(detected_lang, "Please write the explanation in the same language as the report.")

                # Final prompt
                final_prompt = system_prompt + "\n\n" + lang_instruction

                # Format user input
                report_text = f"\"\"\"\n{report_input}\n\"\"\""

                # Get OpenAI API key
                api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

                if not api_key:
                    st.error("❌ OpenAI API key not found. Please set it in .env or Streamlit secrets.")
                    st.stop()

                client = OpenAI(api_key=api_key)

                #client = OpenAI()  # uses key from environment automatically

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": final_prompt},
                        {"role": "user", "content": report_text}
                    ],
                    temperature=0.4,
                    #stream=True
                )

                simplified = response.choices[0].message.content
                st.session_state.usage_count += 1
                st.session_state.simplified = simplified

            except Exception as e:
                st.error("Something went wrong. Please try again.")
                st.exception(e)


if "simplified" in st.session_state:
    simplified = st.session_state.simplified

    detected_lang = st.session_state.get("language", "en")

    lang_name = {
        "en": "English", "de": "German", "fr": "French", "es": "Spanish", "it": "Italian"
    }.get(detected_lang, detected_lang)

    st.success("✅ Simplification complete.")
    st.markdown(f"🌐 Detected report language: **{lang_name}**")
    st.markdown(f"#### ✨ Here’s your simplified explanation:\n{simplified}", unsafe_allow_html=False)
    # lets user copy the result
    #st.code(simplified, language="markdown")
    # lets user download the simplified explanation
    st.download_button("📄 Download Explanation", simplified, file_name="simplified_report.txt")


    # Feedback
    st.markdown("#### 🗣️ Was this explanation helpful?")
    col1, col2 = st.columns(2)
    with col1:
        thumbs_up = st.button("👍 Yes")
    with col2:
        thumbs_down = st.button("👎 No")

    feedback_text = st.text_input(
        "💬 Any suggestions or thoughts?",
        placeholder="Optional. (Type first and click 👍 Yes or 👎 No after)",
        max_chars=300
    )

    # Your actual webhook URL from the Google Apps Script deployment
    WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwTye0hGdBuedw5ujTvkfVneULDhz7YETxuwJjUwiBb5YiprxEciU2kLLo4uPCGeIfVxw/exec"

    if thumbs_up or thumbs_down:
        st.success("Thanks for your feedback!")

        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "feedback": "yes" if thumbs_up else "no",
            "comment": feedback_text.strip()
        }

        try:
            response = requests.post(WEBHOOK_URL, json=feedback_data)
            if response.status_code == 200:
                st.info("✅ Feedback saved.")
            else:
                st.warning("⚠️ Feedback not saved. Please try again.")
        except Exception as e:
            st.error("Error sending feedback.")
            st.exception(e)


# Optional: show usage count
st.markdown(f"<small>🔄 Uses this session: {st.session_state.usage_count}/3</small>", unsafe_allow_html=True)

st.markdown("""
    <div style="
        font-size: 13px;
        color: #888;
        text-align: center;
        margin-top: 4rem;
    ">
        Built by a medical student.<br>
        Designed to save time — and make patients feel confident.
    </div>
""", unsafe_allow_html=True)
