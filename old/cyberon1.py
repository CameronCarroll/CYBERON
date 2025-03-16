import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import json
from pyvis.network import Network

class CyberneticsKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def add_concept(self, name, category, description=None, properties=None):
        """Add a concept node to the graph"""
        self.graph.add_node(name, 
                           type='concept', 
                           category=category,
                           description=description,
                           properties=properties or {})
        
    def add_person(self, name, era=None, contributions=None, description=None):
        """Add a person node to the graph"""
        self.graph.add_node(name, 
                           type='person', 
                           era=era,
                           contributions=contributions or [],
                           description=description)
    
    def add_relationship(self, source, target, relationship_type, properties=None):
        """Add a relationship between nodes"""
        self.graph.add_edge(source, target, 
                           type=relationship_type,
                           properties=properties or {})
    
    def get_related_concepts(self, concept, relationship_type=None):
        """Get concepts related to the given concept"""
        if concept not in self.graph:
            return []
            
        if relationship_type:
            return [target for target in self.graph.neighbors(concept) 
                    if self.graph.edges[concept, target]['type'] == relationship_type]
        else:
            return list(self.graph.neighbors(concept))
    
    def get_concept_path(self, start_concept, end_concept):
        """Find paths between concepts"""
        try:
            return nx.shortest_path(self.graph, start_concept, end_concept)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def visualize(self, output_file='cybernetics_graph.html'):
        """Create an interactive visualization of the graph"""
        net = Network(notebook=False, height="750px", width="100%", directed=True)
        
        # Add nodes with colors based on type
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get('type') == 'person':
                color = '#ff6347'  # Red for people
            else:
                category = attrs.get('category', '')
                # Different colors for different concept categories
                color_map = {
                    'foundations': '#66c2a5',
                    'information_theory': '#fc8d62',
                    'systems_theory': '#8da0cb',
                    'cognitive': '#e78ac3',
                    'ai': '#a6d854',
                    'applications': '#ffd92f'
                }
                color = color_map.get(category, '#cccccc')  # Default gray
                
            net.add_node(node, label=node, title=attrs.get('description', ''), color=color)
        
        # Add edges with labels
        for source, target, attrs in self.graph.edges(data=True):
            net.add_edge(source, target, title=attrs.get('type', ''))
        
        # Set physics layout options
        net.barnes_hut(spring_length=200)
        net.show_buttons()
        net.save_graph(output_file)
        return output_file
    
    def to_json(self, filename=None):
        """Export the graph to JSON format"""
        data = nx.node_link_data(self.graph)
        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        return data
    
    def from_json(self, data_or_filename):
        """Import the graph from JSON format"""
        if isinstance(data_or_filename, str):
            with open(data_or_filename, 'r') as f:
                data = json.load(f)
        else:
            data = data_or_filename
            
        self.graph = nx.node_link_graph(data)
        return self
    
    def query(self, **kwargs):
        """Query nodes based on attributes"""
        results = []
        for node, attrs in self.graph.nodes(data=True):
            match = True
            for key, value in kwargs.items():
                if key not in attrs or attrs[key] != value:
                    match = False
                    break
            if match:
                results.append((node, attrs))
        return results

# Example usage:
def build_sample_graph():
    """Build a sample cybernetics knowledge graph from the ontology"""
    kg = CyberneticsKnowledgeGraph()
    
    # Add key figures
    kg.add_person("Norbert Wiener", "1940s-1960s", ["feedback theory", "cybernetics founding"], 
                 "Mathematician who coined the term 'cybernetics'")
    kg.add_person("W. Ross Ashby", "1940s-1970s", ["law of requisite variety", "homeostasis"], 
                 "Pioneer in systems theory and cybernetics")
    kg.add_person("Claude Shannon", "1940s-1970s", ["information theory"], 
                 "Developed mathematical theory of communication")
    
    # Add core concepts
    kg.add_concept("Cybernetics", "foundations", "The study of control and communication in systems")
    kg.add_concept("First-order cybernetics", "foundations", "Focus on observed systems")
    kg.add_concept("Second-order cybernetics", "foundations", "Including the observer in the system")
    kg.add_concept("Feedback loops", "foundations", "Circular causal processes")
    kg.add_concept("Homeostasis", "foundations", "Self-regulation to maintain stability")
    
    kg.add_concept("Information Theory", "information_theory", "Mathematical study of encoding and transmission of information")
    kg.add_concept("Entropy", "information_theory", "Measure of uncertainty or randomness")
    
    kg.add_concept("Neural Networks", "cognitive", "Computational systems inspired by biological neural networks")
    kg.add_concept("Transformers", "ai", "Neural network architecture based on self-attention mechanisms")
    kg.add_concept("Large Language Models", "ai", "AI systems trained on vast text corpora for language tasks")
    
    # Add relationships
    kg.add_relationship("Norbert Wiener", "Cybernetics", "created")
    kg.add_relationship("Claude Shannon", "Information Theory", "developed")
    kg.add_relationship("W. Ross Ashby", "Homeostasis", "formalized")
    
    kg.add_relationship("Cybernetics", "First-order cybernetics", "evolved_into")
    kg.add_relationship("First-order cybernetics", "Second-order cybernetics", "evolved_into")
    
    kg.add_relationship("Cybernetics", "Feedback loops", "includes_concept")
    kg.add_relationship("Cybernetics", "Homeostasis", "includes_concept")
    
    kg.add_relationship("Information Theory", "Entropy", "defines_concept")
    
    kg.add_relationship("Neural Networks", "Transformers", "evolved_into")
    kg.add_relationship("Transformers", "Large Language Models", "enables")
    
    kg.add_relationship("Cybernetics", "Neural Networks", "influenced")
    kg.add_relationship("Information Theory", "Neural Networks", "provides_foundation_for")
    
    return kg

if __name__ == "__main__":
    # Create a sample graph
    cyber_kg = build_sample_graph()
    
    # Visualize
    html_file = cyber_kg.visualize()
    print(f"Graph visualization saved to {html_file}")
    
    # Export to JSON
    cyber_kg.to_json("cybernetics_kg.json")
    
    # Query examples
    print("\nFoundational concepts:")
    for node, attrs in cyber_kg.query(category="foundations"):
        print(f"- {node}: {attrs.get('description')}")
    
    print("\nPath from Information Theory to LLMs:")
    path = cyber_kg.get_concept_path("Information Theory", "Large Language Models")
    if path:
        print(" -> ".join(path))