import re
import gemini_api
from datetime import datetime
import data_utils
import logging

logger = logging.getLogger("Pricing")

def calculate_price(values, type_produit, artiste, marche, materiaux_selectionnes, is_3d):
    # Get product requirements to determine additional factors
    requirements = gemini_api.get_product_type_requirements(type_produit)
    # Convert requirements to dictionary if it's a string
    if isinstance(requirements, str):
        req_str = requirements.lower()
        requirements = {
            "is_digital": "digital" in req_str,
            "is_3d": any(term in req_str for term in ["3d", "three-dimensional", "sculpture", "installation"]),
            "needs_height": "height" in req_str or "dimension" in req_str,
            "needs_weight": "weight" in req_str or "mass" in req_str,
            "needs_duration": "duration" in req_str or "length" in req_str,
            "needs_resolution": "resolution" in req_str or "quality" in req_str
        }
    is_digital = requirements.get("is_digital", False)
    
    # Market demand
    prompt_market = f"Rate from 1 to 10 the demand for {type_produit} in the {marche} market. Number only."
    market_result = gemini_api.consult_api_gemini(prompt_market)
    match = re.search(r"(\d+)", market_result)
    market_demand = int(match.group(1)) if match else 5

    # Check if the artist is known and get reference price
    is_known = gemini_api.check_known_artist(artiste)
    reference_price = None
    if is_known:
        reference_price = gemini_api.get_artist_price(artiste, type_produit)

    reputation_bonus = 50 if is_known else 0

    # Calculate dimensions based on product type
    height_val = values.get("hauteur", 0) if is_3d or requirements.get("needs_height", False) else 0
    weight_val = values.get("poids", 0) if is_3d or requirements.get("needs_weight", False) else 0
    
    # Process dimensions differently based on digital vs physical
    dimension_factor = 1.0
    if is_digital:
        # For digital products, calculate differently using pixel dimensions
        pixel_area = values["longueur"] * values["largeur"]
        if pixel_area > 0:
            # Normalize pixel dimensions: smaller area = smaller factor
            if pixel_area < 1000000:  # less than 1 megapixel
                dimension_factor = 0.8
            elif pixel_area < 4000000:  # 4 megapixels (2K)
                dimension_factor = 1.0
            elif pixel_area < 8000000:  # 8 megapixels (4K)
                dimension_factor = 1.2
            else:  # 8K and beyond
                dimension_factor = 1.5
            
            dimensions = f"{values["longueur"]}px x {values["largeur"]}px"
        else:
            dimensions = "Unknown"
    elif is_3d:
        # 3D physical object
        volume = values["longueur"] * values["largeur"] * height_val
        dimension_factor = max(1.0, volume / 1000)
        dimensions = f"{values["longueur"]}cm x {values["largeur"]}cm x {height_val}cm"
        weight_info = f"{weight_val} kg"
        weight_factor = max(1.0, weight_val / 5)
        dimension_factor = (dimension_factor + weight_factor) / 2
    else:
        # 2D physical object
        surface = values["longueur"] * values["largeur"]
        dimension_factor = max(1.0, surface / 100)
        dimensions = f"{values["longueur"]}cm x {values["largeur"]}cm"
        
    # Set weight_info for non-3D objects
    weight_info = f"{weight_val} kg" if weight_val > 0 else None

    # Calculate base costs
    base_cost = values["materiaux"] + values["livraison"] + values["pub"]
    time_cost = values["temps"] * 15  # Higher time valuation
    
    # Additional factors from dynamic fields
    additional_factors = 1.0
    
    # Process quality/resolution if available
    if "resolution" in values:
        resolution_value = values["resolution"]
        if isinstance(resolution_value, str):
            if "4K" in resolution_value or "8K" in resolution_value:
                additional_factors *= 1.4
            elif "2K" in resolution_value or "Full HD" in resolution_value:
                additional_factors *= 1.2
            elif "HD" in resolution_value:
                additional_factors *= 1.1
    
    # Process duration if available (for video products)
    if "duration" in values:
        duration_val = values["duration"]
        if duration_val > 0:
            # Longer duration = higher price but with diminishing returns
            duration_factor = min(3.0, 1 + (duration_val / 60))  # Cap at 3x for lengthy videos
            additional_factors *= duration_factor

    # Complexity and rarity factors
    complexity = 1.0 + (len(materiaux_selectionnes) * 0.1)
    market_rarity = 0.8 + (0.05 * market_demand)

    # Calculate final price with all factors
    price = (base_cost + time_cost + reputation_bonus) * complexity * market_rarity * dimension_factor * additional_factors

    # If known artist and reference price available, adjust the price
    if is_known and reference_price:
        price = (price + reference_price) / 2

    # Add digital product premium if applicable
    if is_digital and "resolution" in values:
        # Higher resolution commands premium pricing
        price *= 1.0 + (0.1 * values.get("resolution_factor", 1.0))
    
    # Get recommended price from Gemini
    # Pass additional parameters if they exist
    gemini_price_response = gemini_api.get_starting_price_from_gpt(
        type_produit, artiste, marche, materiaux_selectionnes, 
        dimensions, weight_info,
        values.get("resolution", None),
        values.get("duration", None),
        is_digital
    )

    materials_text = ", ".join(materiaux_selectionnes) if materiaux_selectionnes else "None"

    # Prepare result data
    result = {
        "prix": price,
        "demande_marche": market_demand,
        "dimensions": dimensions,
        "materiaux": materials_text,
        "artiste_connu": is_known,
        "gemini_price": gemini_price_response,
        "height": height_val if is_3d else "",
        "weight": weight_val if is_3d else ""
    }

    # Save data to CSV
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_row = data_utils.format_save_data(
        now, artiste, marche, type_produit, materials_text,
        values["longueur"], values["largeur"],
        height_val if is_3d else "", weight_val if is_3d else "",
        values["materiaux"], values["livraison"], values["pub"],
        values["temps"], f"{price:.2f}", market_demand, gemini_price_response
    )
    data_utils.save_to_file(data_row)
    print("prix", result['prix'])

    return result
