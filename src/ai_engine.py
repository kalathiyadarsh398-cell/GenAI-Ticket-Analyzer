import google.generativeai as genai
import json
from src.config import GEMINI_API_KEY

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY is not set")

model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_ticket(description):

    prompt = f"""
    Analyze this support ticket and return JSON.

    Ticket:
    {description}

    Return:
    {{
        "category":"",
        "priority":"",
        "sentiment":"",
        "summary":""
    }}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)

        return result

    except Exception as e:
        print("Error:", e)

        return {
            "category": "Unknown",
            "priority": "Low",
            "sentiment": "Neutral",
            "summary": "Could not analyze ticket"
        }


def generate_reply(description, policy):

    prompt = f"""
    Customer Issue:
    {description}

    Policy:
    {policy}

    Write a professional support reply.
    """

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print("Error:", e)
        return "Thank you for contacting support."


if __name__ == "__main__":

    ticket = "I was charged twice for my subscription."

    result = analyze_ticket(ticket)

    print(result)