from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Sample flashcards data - will be moved to a separate file later
FLASHCARDS = [
    {
        "id": 1,
        "question": "What command displays the current user's username in the terminal?",
        "answer": "whoami",
        "example": "$ whoami\njohn",
        "category": "User Commands"
    },
    {
        "id": 2,
        "question": "How do you find the current date and time in the terminal?",
        "answer": "Use the date command.",
        "example": "$ date\nWed Oct 18 14:55:02 PDT 2023",
        "category": "System Information"
    }
]

# Simulated command outputs for restricted commands
SIMULATED_OUTPUTS = {
    "passwd": "Changing password for user john.\nNew password: \nRetype new password: \npasswd: all authentication tokens updated successfully.",
    "sudo": "Sorry, user john is not allowed to execute commands as root on localhost."
}

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    """Return all flashcards"""
    return jsonify(FLASHCARDS)

@app.route('/api/flashcards/<int:id>', methods=['GET'])
def get_flashcard(id):
    """Return a specific flashcard"""
    flashcard = next((card for card in FLASHCARDS if card["id"] == id), None)
    if flashcard is None:
        return jsonify({"error": "Flashcard not found"}), 404
    return jsonify(flashcard)

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Handle command execution or simulation"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    # Check if command is in simulated outputs
    if command in SIMULATED_OUTPUTS:
        return jsonify({
            "output": SIMULATED_OUTPUTS[command],
            "simulated": True
        })
    
    # For demonstration, return some safe commands
    if command == "whoami":
        return jsonify({
            "output": "john",
            "simulated": False
        })
    elif command == "date":
        from datetime import datetime
        return jsonify({
            "output": datetime.now().strftime("%c"),
            "simulated": False
        })
    
    # Default response for unknown commands
    return jsonify({
        "output": f"Command '{command}' not supported in demo mode.",
        "simulated": True
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return unique categories from flashcards"""
    categories = list(set(card["category"] for card in FLASHCARDS))
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Changed default port to 5001
    app.run(host='0.0.0.0', port=port, debug=True)
