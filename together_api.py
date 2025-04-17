import requests
import json
import logging
import os

# Set up logging
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logger = logging.getLogger('together_api')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('logs/api.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def call_together_api(keyword):
    """
    Call the Together AI API to get keyword suggestions based on the input keyword.
    
    Args:
        keyword (str): The seed keyword to get suggestions for
        
    Returns:
        dict: A dictionary with success status and either data or error message
    """
    # Together AI API endpoint and key
    url = "https://api.together.xyz/v1/chat/completions"
    api_key = "tgp_v1_TAZIzhzvcLNui9yczKBCpb1hXOGvAl8dKr4buEksnVg"
    
    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prepare the prompt for the AI
    system_prompt = """You are an SEO expert assistant. Your task is to provide keyword suggestions based on the user's input.
For the given keyword or phrase, provide exactly 10 high-ranking SEO keyword suggestions.
For each suggestion, include:
1. The keyword itself
2. A short description (1-2 sentences)
3. The estimated user intent (informational, transactional, navigational, or commercial investigation)
4. A suggested content angle for this keyword
5. An estimated search volume (low, medium, high)
6. A competition score from 1-10 (1 being lowest competition, 10 being highest)

Format your response as a JSON array with objects containing these fields:
[
  {
    "keyword": "example keyword",
    "description": "Short description of the keyword",
    "intent": "User intent category",
    "angle": "Content angle suggestion",
    "volume": "medium",
    "competition": 5
  },
  ...
]
Only return the JSON array, no other text."""
    
    # Prepare the payload with the Together AI model
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Provide SEO keyword suggestions for: {keyword}"}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        logger.info(f"Sending request to Together AI API for keyword: {keyword}")
        # Make the API call
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check for rate limiting or quota exceeded
        if response.status_code == 429:
            logger.error("API rate limit or quota exceeded")
            return {"success": False, "error": "API rate limit or quota exceeded. Please try again later."}
        
        # Check for authentication errors
        if response.status_code == 401:
            logger.error("API authentication failed - invalid API key")
            return {"success": False, "error": "API authentication failed. Please check your API key."}
            
        # Check for model availability
        if response.status_code == 404:
            logger.error("Model not found or unavailable")
            return {"success": False, "error": "The requested AI model is not available. Please try again later."}
        
        # Check for other HTTP errors
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        logger.info("Successfully received response from Together AI API")
        
        # Extract the content from the response
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            
            # Parse the JSON content
            try:
                # Clean the content if it contains markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                keywords_data = json.loads(content)
                
                # Validate the structure of the response
                if not isinstance(keywords_data, list):
                    logger.error("API response is not a list")
                    return {"success": False, "error": "Invalid API response format"}
                
                # Ensure we have at least some results
                if len(keywords_data) == 0:
                    logger.warning("API returned empty results")
                    return {"success": False, "error": "No keyword suggestions found. Please try a different search term."}
                
                # Validate each keyword item has the required fields
                required_fields = ["keyword", "description", "intent", "angle"]
                for item in keywords_data:
                    if not all(key in item for key in required_fields):
                        logger.error("API response missing required fields")
                        return {"success": False, "error": "Invalid API response structure"}
                
                # Add default values for volume and competition if missing
                for item in keywords_data:
                    if "volume" not in item:
                        item["volume"] = "medium"
                    if "competition" not in item:
                        item["competition"] = 5
                
                return {"success": True, "data": keywords_data}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response: {str(e)}")
                logger.error(f"Raw content: {content}")
                return {"success": False, "error": "Failed to parse API response. The service may be experiencing issues."}
        else:
            logger.error("No content in API response")
            return {"success": False, "error": "No content in API response. Please try again."}
            
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return {"success": False, "error": "API request timed out. Please try again later."}
    except requests.exceptions.ConnectionError:
        logger.error("Connection error when calling API")
        return {"success": False, "error": "Connection error. Please check your internet connection and try again."}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {"success": False, "error": f"API request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "error": "An unexpected error occurred. Please try again later."}
