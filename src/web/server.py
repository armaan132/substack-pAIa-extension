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

from index_generator import IndexGenerator
from flask import Flask, request, jsonify, send_from_directory

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PORT = 8000

class Server:
    def __init__(self):
        # Ensure we use the correct data directory relative to project root
        self.generator = IndexGenerator(DATA_DIR)
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
                    from updaters.incremental_update import IncrementalUpdater
                    print("✅ Successfully imported IncrementalUpdater")
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    # Try alternative import path
                    try:
                        from updaters.incremental_update import IncrementalUpdater
                        print("✅ Successfully imported via updaters subdirectory")
                    except ImportError as alt_error:
                        print(f"❌ Alternative import also failed: {alt_error}")
                        raise ImportError(f"Could not import IncrementalUpdater: {import_error}, then {alt_error}")
                
                # Run the incremental update
                print("🚀 Starting incremental update...")
                updater = IncrementalUpdater()
                success = updater.run_incremental_update()
                
                if success:
                    return jsonify({'success': True, 'message': 'Content update completed successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Content update failed'}), 500
                    
            except Exception as e:
                print(f"❌ Error during content update: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # NEW: API endpoint for fast metadata updates (instant)
        @self.flask_app.route('/api/update_metadata', methods=['POST'])
        def update_metadata():
            try:
                print("⚡ Fast metadata update requested via web interface")
                
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                    print("✅ Successfully imported IncrementalUpdater")
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Run only the fast metadata update
                print("🚀 Starting fast metadata update...")
                updater = IncrementalUpdater()
                success = updater.run_pure_config_update()
                
                if success:
                    return jsonify({'success': True, 'message': 'Configuration update completed successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Configuration update failed'}), 500
                    
            except Exception as e:
                print(f"❌ Error during metadata update: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # NEW: API endpoint to check metadata status (fast check)
        @self.flask_app.route('/api/check_metadata_status', methods=['GET'])
        def check_metadata_status():
            try:
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Quick check if newsletters.md has changed
                updater = IncrementalUpdater()
                current_hash = updater.get_newsletter_md_hash()
                
                # Load existing data to get last known hash
                if updater.index_path.exists():
                    with open(updater.index_path, 'r', encoding='utf-8') as f:
                        import json
                        existing_data = json.load(f)
                    last_hash = existing_data.get("newsletter_md_hash")
                else:
                    last_hash = None
                
                needs_update = current_hash != last_hash
                
                return jsonify({
                    'needs_update': needs_update,
                    'current_hash': current_hash,
                    'last_hash': last_hash,
                    'message': 'Metadata update needed' if needs_update else 'No metadata changes detected'
                })
                    
            except Exception as e:
                print(f"❌ Error checking metadata status: {e}")
                return jsonify({'needs_update': False, 'error': str(e)}), 500

        # NEW: API endpoint for structure updates (configuration + post metadata + HTML)
        @self.flask_app.route('/api/update_structure', methods=['POST'])
        def update_structure():
            try:
                print("🔄 Structure update requested via web interface")
                
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                    print("✅ Successfully imported IncrementalUpdater")
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Run structure update (configuration + post metadata + HTML)
                print("🚀 Starting structure update...")
                updater = IncrementalUpdater()
                success = updater.run_structure_update()
                
                if success:
                    return jsonify({'success': True, 'message': 'Structure update completed successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Structure update failed'}), 500
                    
            except Exception as e:
                print(f"❌ Error during structure update: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # NEW: API endpoint for fast link discovery (new posts without content download)
        @self.flask_app.route('/api/discover_links', methods=['POST'])
        def discover_links():
            try:
                print("🚀 Fast link discovery requested via web interface")
                
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                    print("✅ Successfully imported IncrementalUpdater")
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Run fast link discovery
                print("🚀 Starting fast link discovery...")
                updater = IncrementalUpdater()
                success = updater.run_fast_link_discovery()
                
                if success:
                    return jsonify({'success': True, 'message': 'Link discovery completed - new posts visible immediately'})
                else:
                    return jsonify({'success': False, 'error': 'Link discovery failed'}), 500
                    
            except Exception as e:
                print(f"❌ Error during link discovery: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # NEW: API endpoint to get accurate pending downloads count
        @self.flask_app.route('/api/pending_downloads_count', methods=['GET'])
        def get_pending_downloads_count():
            try:
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Get accurate pending downloads count
                updater = IncrementalUpdater()
                count = updater.get_accurate_pending_downloads_count()
                
                return jsonify({
                    'pending_downloads': count,
                    'message': f'{count} posts are currently pending download'
                })
                    
            except Exception as e:
                print(f"❌ Error getting pending downloads count: {e}")
                return jsonify({'pending_downloads': 0, 'error': str(e)}), 500
        
        # NEW: API endpoint to trigger background content downloads
        @self.flask_app.route('/api/download_pending_content', methods=['POST'])
        def download_pending_content():
            try:
                # Import the incremental updater
                import sys
                import os
                from pathlib import Path
                
                project_root = Path(__file__).parent.parent.parent
                scripts_dir = project_root / "scripts"
                
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    from updaters.incremental_update import IncrementalUpdater
                except ImportError as import_error:
                    print(f"❌ Import error: {import_error}")
                    raise ImportError(f"Could not import IncrementalUpdater: {import_error}")
                
                # Start background downloads
                updater = IncrementalUpdater()
                updater.start_background_downloads()
                
                # Get updated count
                count = updater.get_accurate_pending_downloads_count()
                
                return jsonify({
                    'success': True,
                    'message': f'Background downloads started. {count} posts still pending.',
                    'pending_downloads': count
                })
                    
            except Exception as e:
                print(f"❌ Error starting background downloads: {e}")
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
        """Generate required files if they don't exist."""
        try:
            # Check if index.json exists
            json_path = Path("data/index.json")
            if not json_path.exists():
                print("⚠️ index.json missing, regenerating from newsletters.md...")
                self.generator.create_json_index()
            else:
                # NEW: Always run metadata update on server startup (Tier 1 is fast and safe)
                print("🔍 Running metadata update on server startup...")
                try:
                    from updaters.incremental_update import IncrementalUpdater
                    updater = IncrementalUpdater()
                    
                    print("📝 Updating configuration automatically on server startup...")
                    success = updater.run_pure_config_update()
                    if success:
                        print("✅ Configuration updated successfully on server startup")
                    else:
                        print("⚠️ Configuration update failed on server startup")
                        
                except Exception as e:
                    print(f"⚠️ Could not update metadata on startup: {e}")
                    print("   Continuing with existing data...")
            
            # Always generate HTML
            self.generator.create_index_html()
            print("✅ HTML generated successfully")
            
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
