#!/usr/bin/env python3
"""
Build a weighted newsletter graph from the metadata store.

This script reads the metadata store JSON file and creates a graph where:
- Nodes are newsletters
- Edges represent post links between newsletters  
- Edge weights are the count of links from source to target newsletter
"""

import json
import re
from collections import defaultdict
from urllib.parse import urlparse
from pathlib import Path


def extract_newsletter_url(post_url):
    """Extract newsletter URL from a post URL."""
    # Parse the URL and reconstruct the newsletter URL
    parsed = urlparse(post_url)
    # For Substack URLs like: https://newsletter1.substack.com/p/post1
    # We want: https://newsletter1.substack.com
    path_parts = parsed.path.split('/')
    if len(path_parts) >= 2 and path_parts[1] == 'p':
        # This is a post URL, extract the newsletter part
        return f"{parsed.scheme}://{parsed.netloc}"
    else:
        # This might already be a newsletter URL
        return post_url


def build_newsletter_graph(metadata_file):
    """Build weighted newsletter graph from metadata store."""
    
    # Load metadata store
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    # Extract newsletters and posts
    newsletters = data.get('newsletters', [])
    posts = data.get('posts', [])
    
    # Create newsletter lookup for quick access
    newsletter_lookup = {newsletter['url']: newsletter for newsletter in newsletters}
    
    # Initialize edge weights
    edge_weights = defaultdict(int)
    
    # Process each post to build edges
    for post in posts:
        source_newsletter = post['newsletter']
        
        # Skip if source newsletter not found
        if source_newsletter not in newsletter_lookup:
            print(f"Warning: Source newsletter {source_newsletter} not found in newsletters")
            continue
            
        # Process each link in the post
        for linked_post_url in post.get('links_to_substack_posts', []):
            target_newsletter = extract_newsletter_url(linked_post_url)
            
            # Skip self-loops (optional - remove this check if you want self-loops)
            if source_newsletter == target_newsletter:
                continue
                
            # Skip if target newsletter not found
            if target_newsletter not in newsletter_lookup:
                print(f"Warning: Target newsletter {target_newsletter} not found in newsletters")
                continue
            
            # Increment edge weight
            edge_key = (source_newsletter, target_newsletter)
            edge_weights[edge_key] += 1
    
    # Build the graph structure
    graph = {
        'nodes': [],
        'edges': []
    }
    
    # Add nodes (newsletters)
    for newsletter in newsletters:
        node = {
            'id': newsletter['url'],
            'title': newsletter['title'],
            'author': newsletter['author'],
            'topics': newsletter.get('topics', [])
        }
        graph['nodes'].append(node)
    
    # Add edges with weights
    for (source, target), weight in edge_weights.items():
        edge = {
            'source': source,
            'target': target,
            'weight': weight,
            'type': 'post_link'
        }
        graph['edges'].append(edge)
    
    return graph


def save_graph(graph, output_file):
    """Save the graph to a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"Graph saved to {output_file}")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Edges: {len(graph['edges'])}")


def main():
    """Main function to build and save the newsletter graph."""
    
    # File paths
    metadata_file = Path("content/metadata_store.json")
    output_file = Path("content/newsletter_graph.json")
    
    # Check if metadata file exists
    if not metadata_file.exists():
        print(f"Error: Metadata file not found at {metadata_file}")
        return
    
    # Build the graph
    print("Building newsletter graph...")
    graph = build_newsletter_graph(metadata_file)
    
    # Save the graph
    save_graph(graph, output_file)
    
    # Print some statistics
    if graph['edges']:
        weights = [edge['weight'] for edge in graph['edges']]
        print(f"Edge weight statistics:")
        print(f"  Min weight: {min(weights)}")
        print(f"  Max weight: {max(weights)}")
        print(f"  Average weight: {sum(weights) / len(weights):.2f}")


if __name__ == "__main__":
    main()
