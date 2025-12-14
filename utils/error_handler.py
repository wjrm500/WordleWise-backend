import logging
from flask import jsonify, current_app
from http import HTTPStatus

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_error(e, default_message="An unexpected error occurred", status_code=HTTPStatus.INTERNAL_SERVER_ERROR):
    """
    Centralized error handler that logs detailed errors server-side
    and returns safe, generic messages to clients in production.

    Args:
        e: The exception that was caught
        default_message: The generic message to return in production
        status_code: HTTP status code to return (default: 500)

    Returns:
        tuple: (jsonify response, status_code)
    """
    # Log the full error details server-side for debugging
    logger.error(f"Error occurred: {type(e).__name__}: {str(e)}", exc_info=True)

    # Check if we're in development mode
    is_development = current_app.config.get('FLASK_ENV') == 'development'

    # If the exception has a custom 'code' attribute (like custom exceptions),
    # use that status code instead
    if hasattr(e, 'code') and isinstance(e.code, int):
        status_code = e.code

    # In development, return detailed error information
    if is_development:
        error_response = {
            'error': str(e),
            'type': type(e).__name__
        }
    else:
        # In production, return generic error message
        # Only include the original error message if it's a safe, user-facing exception
        if hasattr(e, 'code') and isinstance(e.code, int) and status_code < 500:
            # Client errors (4xx) often contain safe, user-facing messages
            error_response = {'error': str(e)}
        else:
            # Server errors (5xx) should not expose internal details
            error_response = {'error': default_message}

    return jsonify(error_response), status_code


def handle_success_error_response(e, success_key=True):
    """
    Error handler for endpoints that use {'success': True/False, 'error': ...} format.

    Args:
        e: The exception that was caught
        success_key: Whether to include 'success': False in the response

    Returns:
        tuple: (jsonify response, status_code)
    """
    # Log the full error details server-side
    logger.error(f"Error occurred: {type(e).__name__}: {str(e)}", exc_info=True)

    # Check if we're in development mode
    is_development = current_app.config.get('FLASK_ENV') == 'development'

    # Determine status code
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    if hasattr(e, 'code') and isinstance(e.code, int):
        status_code = e.code

    # Build response
    response = {}
    if success_key:
        response['success'] = False

    # In development, show detailed errors
    if is_development:
        response['error'] = str(e)
    else:
        # In production, show generic message for server errors
        if status_code >= 500:
            response['error'] = "An unexpected error occurred"
        else:
            # Client errors can show the actual message (usually safe)
            response['error'] = str(e)

    return jsonify(response), status_code
