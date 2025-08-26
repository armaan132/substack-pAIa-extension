#!/usr/bin/env python3
"""
Test script for the enhanced incremental update functionality.
This script tests the new metadata update methods without running the full update.
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.web.updaters.incremental_update import IncrementalUpdater

def test_metadata_update():
    """Test the metadata update functionality."""
    print("🧪 Testing Enhanced Incremental Update Functionality")
    print("=" * 60)
    
    # Initialize the updater
    updater = IncrementalUpdater()
    
    # Load current newsletter configuration
    from src.web.index_generator import IndexGenerator
    index_generator = IndexGenerator(updater.base_dir)
    current_newsletters = index_generator.load_newsletters_with_categories()
    
    print(f"📋 Loaded {len(current_newsletters)} newsletters from newsletters.md")
    
    # Load existing data (if it exists)
    if updater.index_path.exists():
        with open(updater.index_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
    else:
        print("⚠️ No existing index.json found - creating sample data for testing")
        existing_data = {
            "newsletters": {},
            "categories": {},
            "generated_at": "2025-01-01T00:00:00Z"
        }
    
    # Test metadata update methods
    print("\n🔍 Testing metadata update methods...")
    
    # Test 1: Update existing newsletter metadata
    print("\n1️⃣ Testing update_existing_newsletter_metadata...")
    updated_data = updater.update_existing_newsletter_metadata(current_newsletters, existing_data.copy())
    
    # Test 2: Update post metadata for category changes
    print("\n2️⃣ Testing update_post_metadata_for_category_changes...")
    updated_data = updater.update_post_metadata_for_category_changes(updated_data)
    
    # Test 3: Handle removed newsletters
    print("\n3️⃣ Testing handle_removed_newsletters...")
    updated_data = updater.handle_removed_newsletters(current_newsletters, updated_data)
    
    # Test 4: Detect URL changes
    print("\n4️⃣ Testing detect_url_changes...")
    updated_data = updater.detect_url_changes(current_newsletters, updated_data)
    
    # Test 5: Regenerate category index
    print("\n5️⃣ Testing regenerate_category_index...")
    updated_data = updater.regenerate_category_index(updated_data)
    
    # Test 6: Validate newsletter coverage
    print("\n6️⃣ Testing validate_newsletter_coverage...")
    updater.validate_newsletter_coverage(current_newsletters, updated_data)
    
    # Test 7: Show summary
    print("\n7️⃣ Testing summarize_metadata_changes...")
    updater.summarize_metadata_changes(current_newsletters, updated_data)
    
    print("\n✅ All tests completed!")
    print("\n📊 Summary of changes:")
    print(f"  - Original newsletters: {len(existing_data.get('newsletters', {}))}")
    print(f"  - Updated newsletters: {len(updated_data.get('newsletters', {}))}")
    print(f"  - Original categories: {len(existing_data.get('categories', {}))}")
    print(f"  - Updated categories: {len(updated_data.get('categories', {}))}")
    
    # Show what categories were found
    if "categories" in updated_data:
        print("\n📂 Final category structure:")
        for main_cat, subcats in updated_data["categories"].items():
            print(f"  📁 {main_cat}: {len(subcats)} subcategories")
            for sub_cat in subcats:
                print(f"    📄 {sub_cat}")

if __name__ == "__main__":
    test_metadata_update()
