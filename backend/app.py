"success": True
            })
        elif "-a" in args:
            # Show hidden files
            files = ' '.join(sorted(command_state['mock_files'].keys()))
            return jsonify({
                "output": files,
                "simulated": True,
                "success": True
            })
        elif "-l" in args:
            # Long format listing
            output = "total 64\n"
            for name, info in sorted(command_state['mock_files'].items()):
                if not name.startswith('.'):  # Skip hidden files unless -a is present
                    output += f"{info['perms']} 1 {info['owner']} {info['group']} {info['size']} {info['date']} {name}"
                    if info['type'] == 'link':
                        output += f" -> {info['target']}"
                    output += "\n"
            return jsonify({
                "output": output.rstrip(),
                "simulated": True,
                "success": True
            })
    
    # Handle echo commands
    elif base_command == "echo":
        if len(args) == 1:
            arg = args[0]
            if arg.startswith('\\'):
                # Handle escaped characters
                return jsonify({
                    "output": arg[1:],
                    "simulated": True,
                    "success": True
                })
            elif arg.startswith('$'):
                # Variable expansion
                var_name = arg[1:].strip('{}')
                if var_name in command_state['env_vars']:
                    return jsonify({
                        "output": command_state['env_vars'][var_name],
                        "simulated": True,
                        "success": True
                    })
            elif arg.startswith('~'):
                # Tilde expansion
                user = arg[1:] or 'user'
                if user == 'user' or user == 'root':
                    home_dir = '/root' if user == 'root' else f'/home/{user}'
                    return jsonify({
                        "output": home_dir,
                        "simulated": True,
                        "success": True
                    })
                else:
                    # Return unchanged for nonexistent users
                    return jsonify({
                        "output": arg,
                        "simulated": True,
                        "success": True
                    })
            elif '{' in arg and '}' in arg:
                # Handle brace expansion
                expanded = expand_brace(arg)
                return jsonify({
                    "output": ' '.join(expanded),
                    "simulated": True,
                    "success": True
                })
            else:
                # Regular echo
                return jsonify({
                    "output": arg,
                    "simulated": True,
                    "success": True
                })
    
    # Default response for unknown commands
    return jsonify({
        "output": f"Command not recognized. Please try again.",
        "simulated": True
    })

@app.route('/api/levels', methods=['GET'])
def get_levels():
    """Return all levels"""
    return jsonify(load_levels())

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    """Return all flashcards"""
    return jsonify(get_all_flashcards())

@app.route('/api/flashcards/<int:id>', methods=['GET'])
def get_flashcard(id):
    """Return a specific flashcard"""
    flashcards = get_all_flashcards()
    flashcard = next((card for card in flashcards if card["id"] == id), None)
    if flashcard is None:
        return jsonify({"error": "Flashcard not found"}), 404
    return jsonify(flashcard)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return unique categories from flashcards"""
    flashcards = get_all_flashcards()
    categories = list(set(card["category"] for card in flashcards))
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
