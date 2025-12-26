#!/usr/bin/env python3
"""
Minimal LLM Test - Just the core LLM graph generation code
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm_application import QALLMApplication

# Initialize and generate graph using LLM
qa_app = QALLMApplication()
graph = qa_app.generate_qa_graph()

# Display results
print(f"LLM Generated Graph:")
print(f"Nodes: {len(graph.nodes)}")
print(f"Edges: {len(graph.edges)}")

for node in graph.nodes:
    print(f"- {node.id}: {node.type} ({node.phase})")