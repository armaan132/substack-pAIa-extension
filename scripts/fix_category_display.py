#!/usr/bin/env python3
"""
Fix category display issue in existing index.json.
This script corrects category fields that show "Main > None" to just show "Main".
"""

import json
from pathlib import Path

def fix_category_display():
    """Fix category display in index.json to remove '> None'."""
    json_path = Path("data/index.json")
    
    if not json_path.exists():
        print("❌ index.json not found")
        return
    
    print("🔧 Fixing category display in index.json...")
    
    # Load current JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    
    # Fix newsletter-level category fields
    for newsletter_url, newsletter_data in data.get("newsletters", {}).items():
        main_category = newsletter_data.get("main_category")
        subcategory = newsletter_data.get("subcategory")
        current_category = newsletter_data.get("category", "")
        
        # If subcategory is None/empty and category shows "Main > None", fix it
        if not subcategory and current_category and " > None" in current_category:
            old_category = current_category
            newsletter_data["category"] = main_category
            print(f"  📝 Fixed newsletter {newsletter_data.get('name', newsletter_url)}: '{old_category}' → '{main_category}'")
            fixed_count += 1
        
        # Fix post-level category fields
        for post in newsletter_data.get("posts", []):
            post_main_category = post.get("main_category")
            post_subcategory = post.get("subcategory")
            post_category = post.get("category", "")
            
            # If post subcategory is None/empty and category shows "Main > None", fix it
            if not post_subcategory and post_category and " > None" in post_category:
                old_post_category = post_category
                post["category"] = post_main_category
                print(f"    📝 Fixed post '{post.get('title', 'Unknown')}': '{old_post_category}' → '{post_main_category}'")
                fixed_count += 1
    
    if fixed_count > 0:
        # Save updated JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Fixed {fixed_count} category display issues")
    else:
        print("✅ No category display issues found")
    
    return fixed_count

if __name__ == "__main__":
    fix_category_display()
