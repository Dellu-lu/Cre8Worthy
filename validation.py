import gemini_api
import logging
import sys

# Configure logging
logger = logging.getLogger("ValidationModule")
logger.setLevel(logging.DEBUG)

# Check if handler already exists to avoid duplicate logs
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def validate_numeric_input(value, field_name, error_labels):
    logger.debug(f"Validating numeric input for {field_name}: {value}")
    try:
        value = float(value)
        if value < 0:
            error_labels[field_name].config(text="Must be positive")
            logger.debug(f"Validation failed: {field_name} must be positive")
            return None, True
        logger.debug(f"Validation successful for {field_name}: {value}")
        return value, False
    except ValueError:
        error_labels[field_name].config(text="Number required")
        logger.debug(f"Validation failed: {field_name} requires a number")
        return None, True

def validate_text_input(value, field_name, error_labels):
    logger.debug(f"Validating text input for {field_name}: {value}")
    if not value:
        error_labels[field_name].config(text="Field required")
        logger.debug(f"Validation failed: {field_name} is required")
        return False
    elif not all(c.isalpha() or c.isspace() for c in value):
        error_labels[field_name].config(text="Invalid format")
        logger.debug(f"Validation failed: {field_name} has invalid format")
        return False
    logger.debug(f"Validation successful for {field_name}")
    return True

def validate_type_product(type_produit, custom_type=None):
    logger.debug(f"Validating product type: {type_produit}, custom_type: {custom_type}")
    if not type_produit:
        logger.debug("Validation failed: No product type selected")
        return False, "Please select a product type."

    if type_produit == "Other":
        if not custom_type:
            logger.debug("Validation failed: Custom type not specified")
            return False, "Please specify the product type."
        
        logger.debug(f"Validating custom product type with Gemini API: {custom_type}")
        is_valid = gemini_api.verifier_produit_artistique(custom_type)
        if not is_valid:
            logger.debug(f"Validation failed: '{custom_type}' is not recognized as a valid artistic product")
            return False, f"'{custom_type}' is not recognized as a valid artistic product."
        logger.debug(f"Custom product type validation successful: {custom_type}")

    logger.debug(f"Product type validation successful: {type_produit}")
    return True, ""

def validate_materials(materiaux_selectionnes, type_produit, bypass_api=True):
    """
    Validates if the selected materials are appropriate for the product type.
    
    Args:
        materiaux_selectionnes: List of selected materials
        type_produit: Product type
        bypass_api: If True, bypasses the API call for testing purposes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    logger.debug(f"Validating materials for {type_produit}: {materiaux_selectionnes}, bypass_api: {bypass_api}")
    if not materiaux_selectionnes:
        logger.debug("Validation failed: No materials selected")
        return False, "Please select at least one material."

    # For testing purposes, bypass the API call
    if bypass_api:
        logger.debug("API validation bypassed")
        return True, ""
        
    # Normal validation using the API
    logger.debug(f"Validating materials combination with Gemini API")
    if not gemini_api.verifier_combinaison_materiaux(type_produit, materiaux_selectionnes):
        logger.debug(f"Validation failed: Invalid materials combination for {type_produit}")
        return False, f"The combination of materials {', '.join(materiaux_selectionnes)} is not realistic for a {type_produit}."

    logger.debug("Materials validation successful")
    return True, ""

def validate_market(value, field_name, error_labels):
    """
    Validates a market by calling GPT or performing any necessary checks.
    This simple example just ensures the field is not empty.
    """
    logger.debug(f"Validating market: {value}")
    if not value.strip():
        error_labels[field_name].config(text="Invalid market")
        logger.debug("Validation failed: Empty market")
        return False

    # TODO: Integrate GPT call here if needed.
    # For example:
    # result_from_gpt = consult_api_gpt(f"Is '{value}' a valid market?")
    # if "invalid" in result_from_gpt.lower():
    #     error_labels[field_name].config(text="Market not recognized")
    #     return False

    # If no issues, clear any previous error
    error_labels[field_name].config(text="")
    logger.debug("Market validation successful")
    return True
