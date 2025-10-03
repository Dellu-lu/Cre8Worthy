"""
Gemini API integration for the Cre8Worthy application.
"""
import google.generativeai as genai
import re
import logging
import sys
import datetime
import sqlite3
import os
from config import GEMINI_API_KEY, DB_FILE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("GeminiAPI")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def setup_database():
    """Set up the SQLite database for storing Gemini interactions"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gemini_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        request_type TEXT,
        prompt TEXT,
        response TEXT,
        duration REAL
    )
    ''')
    
    conn.commit()
    conn.close()

def store_interaction(request_type, prompt, response, duration):
    """Store a Gemini API interaction in the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO gemini_interactions (timestamp, request_type, prompt, response, duration) VALUES (?, ?, ?, ?, ?)",
        (timestamp, request_type, prompt, response, duration)
    )
    
    conn.commit()
    conn.close()

def get_all_interactions():
    """Get all stored Gemini interactions"""
    if not os.path.exists(DB_FILE):
        setup_database()
        return []
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, timestamp, request_type, prompt, response, duration FROM gemini_interactions ORDER BY timestamp DESC")
    interactions = cursor.fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries for easier access
    result = []
    for interaction in interactions:
        result.append({
            "id": interaction[0],
            "timestamp": interaction[1],
            "request_type": interaction[2],
            "prompt": interaction[3],
            "response": interaction[4],
            "duration": interaction[5]
        })
    
    return result

# Initialize database on module load
setup_database()

def consult_api_gemini(prompt, request_type="general"):
    """
    Consult Google's Gemini AI model with the given prompt.
    """
    start_time = datetime.datetime.now()
    try:
        logger.debug(f">>> GEMINI API REQUEST: {prompt}")
        # Initialize Gemini with the gemini-pro model
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        
        # Generate a response
        response = model.generate_content(prompt)
        
        # Return the text content from the response
        response_text = response.text
        logger.debug(f"<<< GEMINI API RESPONSE: {response_text[:200]}..." if len(response_text) > 200 else f"<<< GEMINI API RESPONSE: {response_text}")
        
        # Calculate duration in seconds
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Store the interaction
        store_interaction(request_type, prompt, response_text, duration)
        
        return response_text
    except Exception as e:
        error_msg = f"API Error: {str(e)}"
        logger.error(error_msg)
        
        # Record the error too
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        store_interaction(request_type, prompt, error_msg, duration)
        
        return error_msg

def get_starting_price_from_gpt(type_produit, artiste, marche, materiaux, dimensions, poids=None, 
                              resolution=None, duration=None, is_digital=False):
    """
    Enhanced pricing query that takes into account more product details like resolution and duration.
    """
    logger.debug(f"Getting price for {type_produit} by {artiste} in {marche}")
    # Build additional details based on what's provided
    additional_details = []
    
    if resolution:
        additional_details.append(f"resolution: {resolution}")
        
    if duration:
        additional_details.append(f"duration: {duration} minutes")
        
    if poids:
        additional_details.append(f"weight: {poids}")
        
    if is_digital:
        additional_details.append("digital format")
        
    # Add all details to prompt
    details_text = ", ".join(additional_details) if additional_details else ""
    
    prompt = f"""
    As artist {artiste} selling a {type_produit} in the {marche} market, with materials: {', '.join(materiaux)},
    dimensions: {dimensions}{f', {details_text}' if details_text else ''}.
    Give ONLY a recommended price range in euros, as a single number or a brief range (e.g., '1200-1500').
    """
    return consult_api_gemini(prompt, "price_recommendation")

def verify_material_combination(type_produit, materiaux):
    """
    Verify if the combination of materials is realistic for the product type.
    """
    logger.debug(f"Verifying materials {materiaux} for {type_produit}")
    prompt = f"Is this combination of materials: {', '.join(materiaux)} realistic/feasible for creating a {type_produit}? Answer ONLY with 'yes' or 'no'."
    response = consult_api_gemini(prompt, "material_combination_check").lower()
    return "yes" in response

def check_known_artist(artiste):
    """
    Check if an artist is known or recognized.
    """
    logger.debug(f"Checking if artist {artiste} is known")
    prompt = f"Is {artiste} a known/recognized artist? Answer ONLY with 'yes' or 'no'."
    response = consult_api_gemini(prompt, "artist_recognition").lower()
    return "yes" in response

def get_artist_price(artiste, type_produit):
    """
    Get the typical price range for an artist's work.
    """
    logger.debug(f"Getting price range for {artiste}'s {type_produit}")
    prompt = f"What is the average price or typical price range for {type_produit}s by artist {artiste} based on previous sales? Give ONLY a number or brief range in euros."
    response = consult_api_gemini(prompt, "artist_price_check")

    # Try to extract a numeric value from the response
    matches = re.findall(r'(\d+(?:\s*\d+)*)', response)
    if matches:
        # Take the average if there's a range
        nums = [int(re.sub(r'\s', '', m)) for m in matches]
        result = sum(nums) / len(nums)
        logger.debug(f"Extracted price: {result}")
        return result
    return None

def verify_artistic_product(type_produit):
    """
    Verify if the product type is a valid artistic product.
    """
    logger.debug(f"Verifying product type: {type_produit}")
    prompt = f"Is {type_produit} a valid type of artistic product? Answer ONLY with 'yes' or 'no'."
    response = consult_api_gemini(prompt, "product_type_validation").lower()
    return "yes" in response

def verify_material(materiau):
    """
    Verify if a material is valid for artistic products.
    """
    logger.debug(f"Verifying material: {materiau}")
    prompt = f"Is {materiau} a valid material for artistic products? Answer ONLY with 'yes' or 'no'."
    response = consult_api_gemini(prompt, "material_validation").lower()
    return "yes" in response

def get_product_type_requirements(type_produit):
    """
    Get the requirements and specifications for a product type.
    """
    logger.debug(f"Getting requirements for product type: {type_produit}")
    prompt = f"""
    For an artistic product of type '{type_produit}', which of the following characteristics are generally necessary?
    Answer ONLY in the form of a Python dictionary with the following keys and 'true' or 'false' values:
    {{
        "needs_height": true/false,
        "needs_weight": true/false,
        "needs_resolution": true/false,
        "needs_duration": true/false,
        "is_2d": true/false,
        "is_3d": true/false,
        "is_digital": true/false
    }}
    """
    return consult_api_gemini(prompt, "product_requirements")

def validate_materials_with_gpt(materials, type_produit):
    """
    Validate a list of materials against a product type using GPT.
    """
    logger.debug(f"Validating materials {materials} for {type_produit}")
    prompt = f"""Are these materials: {', '.join(materials)} suitable for creating a {type_produit}?
    Answer only with 'yes' or 'no'."""
    response = consult_api_gemini(prompt, "material_validation").lower()
    return "yes" in response

def get_recommended_materials(product_type):
    """
    Get recommended materials for a given product type using Gemini API.
    Returns a dict with 'canvas' and 'other' keys.
    """
    logger.debug(f"Getting recommended materials for product type: {product_type}")
    prompt = f"""
    For an artistic product of type '{product_type}', list the most commonly used materials.
    Answer ONLY in the following JSON format:
    {{
        "canvas": ["..."],   // List of base/support materials
        "other": ["..."]     // List of other materials or techniques
    }}
    Do not include any explanation or text outside the JSON.
    """
    response = consult_api_gemini(prompt, "material_recommendation")
    import json
    # Try to extract and parse JSON robustly
    try:
        # Remove any leading 'json' or whitespace
        response = response.strip()
        if response.lower().startswith('json'):
            response = response[4:].strip()
        # Find the first '{' and last '}' and extract the JSON substring
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            response = response[start:end+1]
        materials = json.loads(response)
        if isinstance(materials, dict) and ("canvas" in materials or "other" in materials):
            return materials
    except Exception as e:
        logger.error(f"Failed to parse materials JSON: {e}")
    # Fallback: parse as comma-separated list
    materials = [mat.strip() for mat in response.split(',') if mat.strip()]
    if materials:
        mid = len(materials) // 2
        return {"canvas": materials[:mid], "other": materials[mid:]}
    # Final fallback: defaults
    return {
        "canvas": ["Canvas", "Cotton", "Linen", "Silk", "Paper", "Other"],
        "other": ["Wood", "Acrylic", "Oil", "Clay", "Metal", "Glass", "Plastic", "Other"]
    }

