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
        
        # API endpoint for triggering incremental content update
        @self.flask_app.route('/api/update_content', methods=['POST'])
        def update_content():
            try:
                print("🔄 Incremental update requested via web interface")
                
                # Import the incremental updater with better path handling
                import sys
                import os
                from pathlib import Path
                
                # Add multiple possible paths
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                # Ensure scripts directory is in Python path
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                print(f"🔍 Python path includes: {sys.path[:3]}...")
                print(f"🔍 Scripts directory: {scripts_dir}")
                
                try:
                    from incremental_update import IncrementalUpdater
                    print("✅ Successfully imported IncrementalUpdater")
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    # Try alternative import path
                    try:
                        from .updaters.incremental_update import IncrementalUpdater
                        print("✅ Successfully imported via scripts.incremental_update")
                    except ImportError as alt_error:
                        print(f"❌ Alternative import also failed: {alt_error}")
                        raise ImportError(f"Could not import IncrementalUpdater: {import_error}, then {alt_error}")
                
                # Run the incremental update
                print("🚀 Starting incremental update...")
                updater = IncrementalUpdater()
                success = updater.run_incremental_update()
                
                if success:
                    message = "Content updated successfully. New posts and sources have been added."
                    print("✅ Update completed successfully")
                    return jsonify({'success': True, 'message': message})
                else:
                    print("❌ Update process failed")
                    return jsonify({'success': False, 'error': 'Update process failed'})
                    
            except Exception as e:
                print(f"❌ Error during incremental update: {e}")
                import traceback
                traceback.print_exc()
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
        """Generate HTML from existing JSON (JSON is source of truth)."""
        try:
            # Check if index.json exists
            json_path = Path("data/index.json")
            if not json_path.exists():
                print("⚠️ index.json missing, regenerating from newsletters.md...")
                print("🔄 This will create a fresh index.json with newsletter structure")
                self.generator.create_json_index()
                print("✅ Fresh index.json created from newsletters.md")
            
            # JSON is the source of truth - use existing or newly created
            print("📝 Using index.json as source of truth")
            
            # Step 1: Initialize personalization fields for existing posts (preserve JSON)
            print("🔧 Initializing personalization fields...")
            self.generator.initialize_personalization_fields()
            
            # Step 2: Generate HTML from the JSON data (JSON controls what exists)
            print("📝 Generating index.html from JSON...")
            self.generator.create_index_html()
            
            print("✅ HTML generated from index.json (JSON preserved as source of truth)")
            
        except Exception as e:
            print(f"❌ Error generating files: {e}")
            raise

def main():
    print("🚀 Starting newsletter personalization server...")
    
    # Initialize the server with the correct base directory
    server = Server()
    
    try:
        # Generate HTML from existing JSON on startup (JSON is source of truth)
        server.generate_files()
        
        print("✅ HTML generated from existing JSON on startup")
        
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
