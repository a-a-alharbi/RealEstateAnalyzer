#!/usr/bin/env python3
"""
Main entry point for the Flask Real Estate Investment Evaluator
This file serves as the deployment entry point for Replit.
"""

import os
from flask_app import app

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask app
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False  # Set to False for production deployment
    )