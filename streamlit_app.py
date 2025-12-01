
import streamlit as st
import json
import ast
from ai_processing import identify_ingredients, generate_recipe, generate_recipe_video

# --- 1. SET UP THE PAGE AND THEME ---
st.set_page_config(
    page_title="AI Recipe Recommender",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NEW: CSS STYLING WITH BACKGROUND COLOR CHANGES
st.markdown("""
<style>
/* 5. PAGE BACKGROUND COLOR (New Addition) */
/* Targets the overall app background (main content area) */
.stApp {
    background-color: #d9cece; /* Very subtle light pink for contrast */
}

/* Targets the sidebar background color */
.st-emotion-cache-vk3wp0 {
    background-color: #F8F8F8; /* Slightly different shade for the sidebar */
}

/* 1. Target the button element inside the stButton div. This is a powerful hack. */
div.stButton > button {
    background-color: #4CAF50; /* Primary Green */
    color: white; /* White text */
    font-weight: bold;
    border-radius: 8px; 
    border: 1px solid #4CAF50; 
    transition: background-color 0.3s, transform 0.3s;
}

/* 2. Style the Hover Effect (crucial for good UI/UX) */
div.stButton > button:hover {
    background-color: #45a049; /* Slightly darker green on hover */
    border-color: #45a049;
    transform: scale(1.02); /* Subtle enlargement on hover */
}

/* 3. Style the Title (optional aesthetic touch) */
h1 {
    color: #4CAF50; 
    border-bottom: 2px solid #eee;
    padding-bottom: 10px;
}

/* 4. Style Success/Alert Messages (using the data-testid) */
div[data-testid="stAlert"] {
    border-radius: 15px; 
    box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1); 
}
</style>
""", unsafe_allow_html=True)


st.title("📸 AI Recipe Recommender")
st.caption("A Multimodal AI Application for the Final Project")
st.markdown("Upload a photo of your fridge contents and constraints, and let the AI craft a unique, delicious recipe.")


# --- 2. USER INPUTS (The UI/UX in the Sidebar) ---
with st.sidebar:
    st.header("⚙️ Recipe Constraints")

    # Constraint 1: Cuisine Type
    cuisine = st.selectbox(
        "Preferred Cuisine:",
        ['Any', 'Italian', 'Asian', 'Mexican', 'Comfort Food', 'Mediterranean']
    )

    # Constraint 2: Max Prep Time
    max_time = st.slider(
        "Max Prep Time (minutes):",
        min_value=15, max_value=90, value=30, step=15
    )
    
    # Constraint 3: Dietary Filter
    dietary_filters = st.multiselect(
        "Dietary Filters:",
        ['Vegetarian', 'Vegan', 'Gluten-Free', 'Low-Carb', 'Nut-Free']
    )

    st.subheader("Ingredient Photo")
    # Image Upload
    uploaded_file = st.file_uploader(
        "Upload a photo of your ingredients:",
        type=['jpg', 'jpeg', 'png']
    )

    generate_button = st.button("Generate Recipe", type="primary", use_container_width=True)


# --- 3. CORE WORKFLOW LOGIC AND VIDEO INTEGRATION ---

# Initialize session state variable to store the generated recipe data
if 'recipe_data' not in st.session_state:
    st.session_state.recipe_data = None
    st.session_state.video_url = None
    st.session_state.narration_script = None

# --- A. Recipe Generation Logic ---
if generate_button and uploaded_file is not None:
    st.info("Step 1: Analyzing Ingredients...")
    
    col1, col2 = st.columns([1, 2]) 
    
    with col1:
        st.image(uploaded_file, caption="Uploaded Ingredients", use_container_width=True) 
    
    with col2:
        with st.spinner('Analyzing your photo and detecting food items...'):
            ingredient_list_str = identify_ingredients(uploaded_file) 
    
    if ingredient_list_str and "FAILURE: NO FOOD DETECTED" in ingredient_list_str:
        st.error("❌ Ingredient identification failed. No discernible food items were detected in your image.")
        st.session_state.recipe_data = None
    elif "Error" in ingredient_list_str:
         st.error(f"A technical error occurred during ingredient identification. Details: {ingredient_list_str}")
         st.session_state.recipe_data = None
    elif ingredient_list_str:
        
        st.success("✅ Ingredients Identified. Starting Recipe Generation...")
        
        with st.expander("📝 View Identified Ingredients"):
            try:
                clean_list = ast.literal_eval(ingredient_list_str)
                st.markdown("\n".join([f"- **{i}**" for i in clean_list]))
            except:
                st.code(ingredient_list_str) 


        st.info("Step 2: Generating Personalized Recipe...")
        with st.spinner('Crafting the perfect dish based on your constraints...'):
            recipe_json_str = generate_recipe(
                ingredient_list_str, 
                cuisine, 
                max_time, 
                dietary_filters
            )
        
        try:
            recipe_data = json.loads(recipe_json_str) 
            st.session_state.recipe_data = recipe_data # Store data
            st.session_state.narration_script = recipe_data.get('narration_script', 'No script generated.')

        except json.JSONDecodeError:
            st.error("Error: Could not parse the recipe. The AI did not return a valid JSON structure.")
            with st.expander("View Raw AI Output (for debugging)"):
                 st.code(recipe_json_str)
            st.session_state.recipe_data = None

# --- B. Display Recipe and Video Button ---
if st.session_state.recipe_data:
    data = st.session_state.recipe_data

    st.header("🍽️ Your Custom AI Recipe!")
    st.subheader(f"**{data.get('title', 'A Delightful Creation')}**")
    
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Prep Time", f"{data.get('prep_time_minutes', '?')} min")
    meta_col2.metric("Cuisine", data.get('cuisine', cuisine))
    meta_col3.metric("Dietary", ', '.join(dietary_filters) if dietary_filters else 'Standard')
    
    st.markdown(f"> *{data.get('description', '')}*")
    st.markdown("---") 
    
    final_col1, final_col2 = st.columns(2)
    
    with final_col1:
        st.subheader("Ingredients Used")
        ingredients_list = data.get('ingredients_used', [])
        st.markdown("\n".join([f"**•** {i}" for i in ingredients_list]))
        
    with final_col2:
        st.subheader("Instructions")
        instructions_list = data.get('instructions', [])
        for i, step in enumerate(instructions_list):
            st.markdown(f"**{i+1}.** {step}")

    st.markdown("---") 
    st.subheader("🎥 Step 3: AI-Generated Video Instructions")
    
    # New Video Generation Button
    video_button = st.button("Generate Video Instructions", key="video_gen_btn", type="secondary")
    
    if video_button:
        with st.spinner("Calling Text-to-Video API..."):
            # Call the mock function
            video_url = generate_recipe_video(data.get('title'), st.session_state.narration_script)
            st.session_state.video_url = video_url
            
            st.success("Video link generated!")
            
    if st.session_state.video_url:
        st.info("Enjoy this video if you do not know where to start cooking ")
        st.video(st.session_state.video_url)
        with st.expander("View AI Narration Script"):
            st.code(st.session_state.narration_script)

elif generate_button:
    st.warning("Please upload an image before generating a recipe.")
