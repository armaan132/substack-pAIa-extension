#!/usr/bin/env python3
"""
Main server application for the newsletter personalization system.
Provides both static file serving and interactive API functionality.
"""

import sys
import os
import threading
import time
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .index_generator import IndexGenerator
from flask import Flask, request, jsonify, send_from_directory

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PORT = 8000

class Server:
    def __init__(self):
        self.generator = IndexGenerator()
        self.flask_app = None
        self.server_thread = None
        
    def start_server(self):
        """Start the Flask server with both API and static file serving."""
        if self.flask_app is not None:
            return
        
        self.flask_app = Flask(__name__)
        
        # API endpoint for updating not_interesting field
        @self.flask_app.route('/api/update_not_interesting', methods=['POST'])
        def update_not_interesting():
            try:
                data = request.get_json()
                post_id = data.get('post_id')
                not_interesting = data.get('not_interesting', False)
                
                if not post_id:
                    return jsonify({'success': False, 'error': 'Missing post_id'}), 400
                
                success = self.generator.update_post_not_interesting(post_id, not_interesting)
                if success:
                    # Regenerate HTML to reflect the updated state
                    self.generator.create_index_html()
                return jsonify({'success': success})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API endpoint for updating read field
        @self.flask_app.route('/api/update_read', methods=['POST'])
        def update_read():
            try:
                data = request.get_json()
                post_id = data.get('post_id')
                read = data.get('read', False)
                
                if not post_id:
                    return jsonify({'success': False, 'error': 'Missing post_id'}), 400
                
                success = self.generator.update_post_read(post_id, read)
                if success:
                    # Regenerate HTML to reflect the updated state
                    self.generator.create_index_html()
                return jsonify({'success': success})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        # API endpoint for updating like field
        @self.flask_app.route('/api/update_like', methods=['POST'])
        def update_like():
            try:
                data = request.get_json()
                post_id = data.get('post_id')
                like = data.get('like', False)
                
                if not post_id:
                    return jsonify({'success': False, 'error': 'Missing post_id'}), 400
                
                success = self.generator.update_post_like(post_id, like)
                if success:
                    # Regenerate HTML to reflect the updated state
                    self.generator.create_index_html()
                return jsonify({'success': success})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        # API endpoint for updating hide field
        @self.flask_app.route('/api/update_hide', methods=['POST'])
        def update_hide():
            try:
                data = request.get_json()
                post_id = data.get('post_id')
                hide = data.get('hide', False)
                
                if not post_id:
                    return jsonify({'success': False, 'error': 'Missing post_id'}), 400
                
                success = self.generator.update_post_hide(post_id, hide)
                if success:
                    # Regenerate HTML to reflect the updated state
                    self.generator.create_index_html()
                return jsonify({'success': success})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Serve static files from project root
        @self.flask_app.route('/<path:filename>')
        def serve_file(filename):
            return send_from_directory(str(PROJECT_ROOT), filename)
        
        # Serve root directory
        @self.flask_app.route('/')
        def serve_root():
            return send_from_directory(str(PROJECT_ROOT), 'data/index.html')
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(
            target=lambda: self.flask_app.run(port=PORT, debug=False, host='0.0.0.0')
        )
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"🚀 Started server on port {PORT}")
        print(f"📁 Serving files from {PROJECT_ROOT}")
        print(f"📊 Data directory is at {DATA_DIR}")
        time.sleep(1)  # Give server time to start

    def stop_server(self):
        """Stop the Flask server."""
        if self.flask_app:
            print("🛑 Server will stop when main process exits")

    def generate_files(self):
        """Generate the index files with personalization features (JSON-first approach)."""
        try:
            # Step 1: Generate JSON first (the single source of truth)
            print("📝 Generating index.json (primary data)...")
            self.generator.create_json_index()
            
            # Step 2: Initialize personalization fields for existing posts
            print("🔧 Initializing personalization fields...")
            self.generator.initialize_personalization_fields()
            
            # Step 3: Generate HTML from the JSON data
            print("📝 Generating index.html from JSON...")
            self.generator.create_index_html()
            
            print("✅ All files generated successfully!")
            
        except Exception as e:
            print(f"❌ Error generating files: {e}")
            raise

def main():
    print("🚀 Starting newsletter personalization server...")
    
    # Initialize the server with the correct base directory
    server = Server()
    
    try:
        # Generate the index files first
        server.generate_files()
        
        print("✅ Files generated successfully!")
        
        # Start the server
        server.start_server()
        
        print(f"🌐 Server running on http://localhost:{PORT}")
        print(f"📱 Open http://localhost:{PORT}/data/index.html in your browser")
        print(f"📁 Or just open http://localhost:{PORT}/ for the main page")
        print("⏹️  Press Ctrl+C to stop the server")
        
        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            server.stop_server()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        server.stop_server()
        sys.exit(1)

if __name__ == "__main__":
    main()
