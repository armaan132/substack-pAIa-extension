#!/usr/bin/env python3
"""
Test script for the newsletter graph builder.
"""

import json
import sys
from pathlib import Path

# Add the scripts directory to the path so we can import the graph builder
sys.path.append(str(Path(__file__).parent))

from build_newsletter_graph import build_newsletter_graph


def test_graph_building():
    """Test the graph building functionality."""
    
    # Test data file
    test_file = Path("test_data/test_metadata.json")
    
    if not test_file.exists():
        print(f"Error: Test file not found at {test_file}")
        return False
    
    print("Testing graph building...")
    
    # Build the graph
    graph = build_newsletter_graph(test_file)
    
    # Verify the structure
    if 'nodes' not in graph or 'edges' not in graph:
        print("Error: Graph missing 'nodes' or 'edges' keys")
        return False
    
    print(f"✓ Graph structure is valid")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Edges: {len(graph['edges'])}")
    
    # Check expected results
    expected_nodes = 3
    expected_edges = 3  # newsletter1->newsletter2 (3 links), newsletter2->newsletter3 (1 link), newsletter3->newsletter1 (1 link)
    
    if len(graph['nodes']) != expected_nodes:
        print(f"Error: Expected {expected_nodes} nodes, got {len(graph['nodes'])}")
        return False
    
    if len(graph['edges']) != expected_edges:
        print(f"Error: Expected {expected_edges} edges, got {len(graph['edges'])}")
        return False
    
    print(f"✓ Node and edge counts are correct")
    
    # Check specific edge weights
    edge_lookup = {}
    for edge in graph['edges']:
        key = (edge['source'], edge['target'])
        edge_lookup[key] = edge['weight']
    
    # Expected edges and weights based on test data:
    # newsletter1 -> newsletter2: 3 links (2 from post1, 1 from post2)
    # newsletter2 -> newsletter3: 1 link (from post2)
    # newsletter3 -> newsletter1: 1 link (from post4)
    
    expected_edges = {
        ("https://newsletter1.substack.com", "https://newsletter2.substack.com"): 3,
        ("https://newsletter2.substack.com", "https://newsletter3.substack.com"): 1,
        ("https://newsletter3.substack.com", "https://newsletter1.substack.com"): 1
    }
    
    for (source, target), expected_weight in expected_edges.items():
        actual_weight = edge_lookup.get((source, target), 0)
        if actual_weight != expected_weight:
            print(f"Error: Edge {source} -> {target} has weight {actual_weight}, expected {expected_weight}")
            return False
    
    print(f"✓ Edge weights are correct")
    
    # Print the graph for inspection
    print("\nGenerated graph:")
    print(json.dumps(graph, indent=2))
    
    print("\n✓ All tests passed!")
    return True


def main():
    """Run the test."""
    success = test_graph_building()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
