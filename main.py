import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from mailauto import *
from flask import send_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize email automation
try:
    email_automation = EmailAutomation(
        email_address=os.getenv('EMAIL_ADDRESS'),
        email_password=os.getenv('EMAIL_PASSWORD')
    )
except Exception as e:
    logger.error(f"Failed to initialize EmailAutomation: {e}")
    email_automation = None

@app.route('/', methods=['GET'])
def home():
    """
    Serve the frontend HTML file
    """
    with open('client.html', 'r') as f:
        html_content = f.read()
    return html_content

@app.route('/get-recipe', methods=['POST'])
def get_recipe():
    """
    Handle recipe ingredient requests with comprehensive error handling
    """
    try:
        # Log incoming request details
        logger.info(f"Received request: {request.json}")

        # Validate request data
        if not request.json:
            return jsonify({
                'success': False,
                'message': 'No request data provided'
            }), 400

        # Parse incoming request data
        request_data = request.json
        request_type = request_data.get('type', 'recipe')

        # Validate API key
        api_key = os.getenv('SPOONACULAR_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'Spoonacular API key not configured'
            }), 500

        if request_type == 'recipe':
            # Validate required fields
            food_type = request_data.get('food_type')
            recipient_email = request_data.get('recipient_email')

            if not food_type or not recipient_email:
                return jsonify({
                    'success': False,
                    'message': 'Missing food type or recipient email'
                }), 400

            # Optional parameters
            cuisine = request_data.get('cuisine')
            diet = request_data.get('diet')
            meal_type = request_data.get('type')
            include_ingredients = request_data.get('includeIngredients')
            exclude_ingredients = request_data.get('excludeIngredients')
            max_ready_time = request_data.get('maxReadyTime')

            # Get ingredients with optional filters
            ingredients = email_automation.get_recipe_ingredients(
                food_type, 
                api_key,
                cuisine=cuisine,
                diet=diet,
                meal_type=meal_type,
                include_ingredients=include_ingredients,
                exclude_ingredients=exclude_ingredients,
                max_ready_time=max_ready_time
            )

            if ingredients:
                # Prepare email
                ingredients_list = '\n'.join(ingredients)
                subject = f"Ingredients for {food_type} Recipe"
                body = f"Here are the ingredients for your {food_type} recipe:\n\n{ingredients_list}"

                # Send email
                success, message = email_automation.send_email(recipient_email, subject, body)

                # Prepare response
                return jsonify({
                    'success': success,
                    'message': message,
                    'ingredients': ingredients
                }), 200
            else:
                # No ingredients found
                return jsonify({
                    'success': False,
                    'message': "No ingredients found",
                    'ingredients': []
                }), 404

        elif request_type == 'fetch_emails':
            # Fetch recent emails request
            emails = email_automation.fetch_recent_emails()
            return jsonify({
                'success': True,
                'emails': emails
            }), 200

        else:
            return jsonify({
                'success': False,
                'message': 'Invalid request type'
            }), 400

    except Exception as e:
        # Log the full error for server-side debugging
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)