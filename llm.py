"""Itinerary generation through the OpenAI API."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def generate_itinerary(source, destination, start_date, end_date, no_of_day):
    """Return a day-by-day itinerary, or a readable error string."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY is not set. Add it to your .env file."

    prompt = f"""Generate a personalized trip itinerary for a {no_of_day}-day trip from {source} to {destination}
    on {start_date} to {end_date}, with an optimum budget (Currency: INR).

    Please include:
    - Day-wise breakdown of activities
    - Popular tourist attractions to visit
    - Recommended local restaurants and cuisine
    - Estimated costs for activities and meals
    - Travel tips specific to the destination
    - Best modes of local transport
    """

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a knowledgeable travel planner with expertise in creating detailed travel itineraries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_message = f"Error generating itinerary: {e}"
        print(error_message)
        return error_message
