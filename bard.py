import openai
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Get the API key and add debugging
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No OPENAI_API_KEY found in environment variables. Please check your .env file.")

# Set the API key for openai
openai.api_key = api_key

def generate_itinerary(source, destination, start_date, end_date, no_of_day):
    """
    Generate a travel itinerary using OpenAI's GPT-4o-mini model.
    """
    if not openai.api_key:
        return "Error: OpenAI API key not configured properly."
    
    try:
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

        # Use the correct method for chat completion
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using your specific model
            messages=[
                {"role": "system", "content": "You are a knowledgeable travel planner with expertise in creating detailed travel itineraries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response['choices'][0]['message']['content']  # Updated to access the response correctly
        
    except Exception as e:
        error_message = f"Error generating itinerary: {str(e)}"
        print(error_message)  # For server logs
        return error_message  # To display to user
