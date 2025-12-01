
import os
import json 
from google import genai
from google.genai import types
import streamlit as st # Import streamlit to access st.secrets

# --- 1. GLOBAL CLIENT REMOVED: NO GLOBAL INITIALIZATION ---
# The client is now initialized inside the functions below to ensure the
# Streamlit secret is available at runtime.

# --- 2. AI STEP 1: IDENTIFY INGREDIENTS (LAZY INITIALIZATION) ---
def identify_ingredients(uploaded_file):
    try:
        # LAZY INITIALIZATION: Create the client right before use
        # This guarantees st.secrets is ready.
        client = genai.Client(api_key=st.secrets['GEMINI_API_KEY']) 
    except Exception as e:
        # If the key is missing or invalid, fail cleanly
        print(f"Error during client initialization: {e}")
        return "Error: AI client not initialized."
    
    # Check if the key is empty just in case
    if not st.secrets.get('GEMINI_API_KEY'):
        return "Error: Gemini API key is missing from Streamlit secrets."

    image_bytes = uploaded_file.getvalue()
    
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=uploaded_file.type
    )

    prompt = """
    You are an expert food inventory specialist. Analyze the provided image.
    List every distinct food item and estimate the quantity or amount.
    Output ONLY a Python list of strings. Do not include any introductory or
    explanatory text.
    
    If the image contains absolutely no discernible food ingredients, 
    output the exact phrase: FAILURE: NO FOOD DETECTED
    
    Example format: ['3 large tomatoes', '1/2 red onion', '1 block of feta cheese', 'handful of basil leaves']
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt]
        )
        response_text = response.text.strip().replace("```python", "").replace("```", "")
        return response_text
    except Exception as e:
        print(f"Error during ingredient identification: {e}")
        return f"Error during API call: {e}"

# --- 3. AI STEP 2 & SCRIPT GENERATION: GENERATE RECIPE (LAZY INITIALIZATION) ---
def generate_recipe(ingredient_list_str, cuisine, max_time, dietary_filters):
    # LAZY INITIALIZATION: Create the client right before use
    try:
        client = genai.Client(api_key=st.secrets['GEMINI_API_KEY']) 
    except Exception as e:
        print(f"Error during client initialization: {e}")
        return '{"error": "AI client not initialized."}'

    if "FAILURE: NO FOOD DETECTED" in ingredient_list_str:
        return '{"error": "Ingredient identification failed. No food was detected in the image."}'
        
    constraints = f"""
    Constraints:
    * **Cuisine:** {cuisine}
    * **Dietary:** {', '.join(dietary_filters) if dietary_filters else 'None'}
    * **Max Prep Time:** {max_time} minutes.
    """

    prompt = f"""
    You are a professional, creative recipe developer. Your task is to generate one unique,
    easy-to-follow recipe using ONLY the ingredients listed below.
    Assume the user has salt, pepper, and standard cooking oil.

    **Ingredients:** {ingredient_list_str}

    **{constraints}**

    Format: Present the output in a JSON format. Do not include any other text besides the JSON object.
    Keys must include: `title`, `description`, `cuisine`, `prep_time_minutes`, `ingredients_used` (a list of strings), `instructions` (a list of strings), and a new key, **`narration_script`** (a single string containing a voiceover script summarizing the instructions in a cheerful, clear tone).
    Ensure `prep_time_minutes` adheres to the max time constraint.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )
        return response.text.strip().replace("```json", "").replace("```", "")
    except Exception as e:
        print(f"Error during recipe generation: {e}")
        return '{"error": "Recipe generation failed due to API error."}'


# --- 4. MOCK AI STEP 3: VIDEO GENERATION ---
def generate_recipe_video(recipe_title, narration_script):
    """
    Returns a real YouTube URL that will correctly load and play for demonstration.
    """
    valid_youtube_url = "https://www.youtube.com/watch?v=kY3NfQGz29Q"
    return valid_youtube_url
