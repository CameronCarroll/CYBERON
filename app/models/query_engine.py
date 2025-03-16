import networkx as nx
import json
from typing import List, Dict, Any, Optional, Set, Tuple
import re

class CyberneticsQueryEngine:
    """
    A query engine for exploring and analyzing the cybernetics ontology
    """
    def __init__(self, data_source: str):
        """
        Initialize the query engine with a data source
        
        Args:
            data_source: Path to the JSON file with ontology data,
                         or a dictionary containing the data
        """
        self.load_data(data_source)
        self.build_graph()
        
    def load_data(self, data_source: str) -> None:
        """Load ontology data from JSON file or dictionary"""
        if isinstance(data_source, str):
            with open(data_source, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = data_source
            
        # Extract structured ontology and knowledge graph
        self.structured_ontology = self.data.get("structured_ontology", {})
        self.knowledge_graph = self.data.get("knowledge_graph", {
            "nodes": [],
            "edges": []
        })
    
    def build_graph(self) -> None:
        """Build a NetworkX graph from the knowledge graph data"""
        self.graph = nx.DiGraph()
        
        # Add nodes
        for node in self.knowledge_graph.get("nodes", []):
            self.graph.add_node(
                node["id"],
                label=node.get("label", node["id"]),
                type=node.get("type", "unknown")
            )
        
        # Add edges
        for edge in self.knowledge_graph.get("edges", []):
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                label=edge.get("label", "")
            )
    
    def query_entity(self, entity_id: str) -> Dict:
        """
        Get detailed information about an entity
        
        Args:
            entity_id: ID of the entity to query
            
        Returns:
            Dictionary with entity information
        """
        if entity_id not in self.graph:
            return {"error": f"Entity '{entity_id}' not found"}
        
        # Get node attributes
        attributes = self.graph.nodes[entity_id]
        
        # Get incoming and outgoing connections
        incoming = []
        for source, _, data in self.graph.in_edges(entity_id, data=True):
            source_label = self.graph.nodes[source].get("label", source)
            incoming.append({
                "id": source,
                "label": source_label,
                "relationship": data.get("label", "connected to")
            })
        
        outgoing = []
        for _, target, data in self.graph.out_edges(entity_id, data=True):
            target_label = self.graph.nodes[target].get("label", target)
            outgoing.append({
                "id": target,
                "label": target_label,
                "relationship": data.get("label", "connected to")
            })
        
        return {
            "id": entity_id,
            "attributes": attributes,
            "incoming": incoming,
            "outgoing": outgoing
        }
    
    def find_paths(self, source_id: str, target_id: str, max_length: int = 3) -> List[List[Dict]]:
        """
        Find paths between two entities
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_length: Maximum path length
            
        Returns:
            List of paths, each path is a list of nodes
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        try:
            # Find all simple paths up to max_length
            paths = list(nx.all_simple_paths(
                self.graph, source_id, target_id, cutoff=max_length
            ))
            
            # Convert paths to a more detailed format
            detailed_paths = []
            for path in paths:
                detailed_path = []
                for i, node_id in enumerate(path):
                    node_info = {
                        "id": node_id,
                        "label": self.graph.nodes[node_id].get("label", node_id),
                        "type": self.graph.nodes[node_id].get("type", "unknown")
                    }
                    
                    # Add relationship to next node if not the last node
                    if i < len(path) - 1:
                        next_node = path[i + 1]
                        edge_data = self.graph.get_edge_data(node_id, next_node)
                        relationship = edge_data.get("label", "connected to")
                        node_info["relationship_to_next"] = relationship
                    
                    detailed_path.append(node_info)
                
                detailed_paths.append(detailed_path)
            
            return detailed_paths
        
        except nx.NetworkXNoPath:
            return []
    
    def find_connections(self, entity_id: str, max_distance: int = 2) -> Dict:
        """
        Find all entities connected to the given entity within a certain distance
        
        Args:
            entity_id: ID of the entity
            max_distance: Maximum distance to search
            
        Returns:
            Dictionary mapping distance to a list of connected entities
        """
        if entity_id not in self.graph:
            return {"error": f"Entity '{entity_id}' not found"}
        
        connections = {}
        
        for distance in range(1, max_distance + 1):
            connections[distance] = []
            
            for node in self.graph.nodes():
                if node == entity_id:
                    continue
                
                try:
                    shortest_path_length = nx.shortest_path_length(
                        self.graph, source=entity_id, target=node
                    )
                    
                    if shortest_path_length == distance:
                        connections[distance].append({
                            "id": node,
                            "label": self.graph.nodes[node].get("label", node),
                            "type": self.graph.nodes[node].get("type", "unknown")
                        })
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass
        
        return connections
    
    def search_entities(self, query: str, entity_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for entities matching the query string
        
        Args:
            query: Search query
            entity_types: Optional list of entity types to filter by
            
        Returns:
            List of matching entities
        """
        results = []
        
        query_lower = query.lower()
        for node, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", node).lower()
            node_type = attrs.get("type", "unknown")
            
            if entity_types and node_type not in entity_types:
                continue
                
            if query_lower in label:
                results.append({
                    "id": node,
                    "label": attrs.get("label", node),
                    "type": node_type,
                    "match_score": 1.0 if label == query_lower else 0.5
                })
        
        # Sort by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
    
    def get_central_entities(self, top_n: int = 10) -> List[Dict]:
        """
        Get the most central entities in the ontology based on degree centrality
        
        Args:
            top_n: Number of top entities to return
            
        Returns:
            List of central entities with their centrality scores
        """
        # Calculate degree centrality
        centrality = nx.degree_centrality(self.graph)
        
        # Sort nodes by centrality
        central_nodes = sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Format results
        results = []
        for node_id, score in central_nodes:
            results.append({
                "id": node_id,
                "label": self.graph.nodes[node_id].get("label", node_id),
                "type": self.graph.nodes[node_id].get("type", "unknown"),
                "centrality": score,
                "connections": self.graph.degree(node_id)
            })
        
        return results
    
    def find_communities(self) -> Dict[int, List[str]]:
        """
        Detect communities in the ontology using the Louvain algorithm
        
        Returns:
            Dictionary mapping community ID to list of node IDs
        """
        try:
            import community as community_louvain
            
            # Convert directed graph to undirected for community detection
            undirected_graph = self.graph.to_undirected()
            
            # Detect communities
            partition = community_louvain.best_partition(undirected_graph)
            
            # Group nodes by community
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(node)
            
            return communities
            
        except ImportError:
            # Fallback to connected components if community module not available
            components = list(nx.connected_components(self.graph.to_undirected()))
            
            communities = {}
            for i, component in enumerate(components):
                communities[i] = list(component)
            
            return communities
    
    def get_entity_types(self) -> Dict[str, int]:
        """
        Get a count of entities by type
        
        Returns:
            Dictionary mapping entity type to count
        """
        type_counts = {}
        
        for _, attrs in self.graph.nodes(data=True):
            entity_type = attrs.get("type", "unknown")
            
            if entity_type not in type_counts:
                type_counts[entity_type] = 0
            type_counts[entity_type] += 1
        
        return type_counts
    
    def get_subsection_content(self, section_num: int, subsection_name: str) -> List[str]:
        """
        Get the content of a specific subsection
        
        Args:
            section_num: Section number
            subsection_name: Name of the subsection
            
        Returns:
            List of items in the subsection
        """
        if section_num not in self.structured_ontology:
            return []
            
        section = self.structured_ontology[section_num]
        subsections = section.get("subsections", {})
        
        # Try exact match first
        if subsection_name in subsections:
            return subsections[subsection_name]
        
        # Try case-insensitive match
        for name, content in subsections.items():
            if name.lower() == subsection_name.lower():
                return content
        
        return []
    
    def find_section_by_topic(self, topic: str) -> List[Dict]:
        """
        Find sections that mention a specific topic
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of matching sections
        """
        results = []
        topic_lower = topic.lower()
        
        for section_num, section_data in self.structured_ontology.items():
            section_title = section_data.get("title", "").lower()
            
            # Check if topic is in section title
            title_match = topic_lower in section_title
            
            # Check subsections and their content
            subsection_matches = []
            for subsection_name, items in section_data.get("subsections", {}).items():
                # Check if topic is in subsection name
                if topic_lower in subsection_name.lower():
                    subsection_matches.append({
                        "name": subsection_name,
                        "type": "subsection_title"
                    })
                
                # Check if topic is in any item
                for item in items:
                    if topic_lower in item.lower():
                        subsection_matches.append({
                            "name": subsection_name,
                            "item": item,
                            "type": "item"
                        })
            
            if title_match or subsection_matches:
                results.append({
                    "section_num": section_num,
                    "title": section_data.get("title", ""),
                    "title_match": title_match,
                    "subsection_matches": subsection_matches
                })
        
        return results
    
    def analyze_concept_hierarchy(self) -> Dict:
        """
        Analyze the hierarchy of concepts in the ontology
        
        Returns:
            Dictionary with hierarchy analysis
        """
        # Find root nodes (no incoming edges)
        root_nodes = []
        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) > 0:
                root_nodes.append(node)
        
        # Calculate depth of hierarchy from each root
        max_depths = {}
        hierarchies = {}
        
        for root in root_nodes:
            # BFS to find maximum depth
            visited = {root: 0}  # node -> depth
            queue = [(root, 0)]  # (node, depth)
            
            while queue:
                node, depth = queue.pop(0)
                
                for _, target in self.graph.out_edges(node):
                    if target not in visited:
                        new_depth = depth + 1
                        visited[target] = new_depth
                        queue.append((target, new_depth))
            
            max_depth = max(visited.values()) if visited else 0
            max_depths[root] = max_depth
            
            # Build hierarchy dict
            hierarchy = {}
            for node, depth in visited.items():
                if depth not in hierarchy:
                    hierarchy[depth] = []
                hierarchy[depth].append({
                    "id": node,
                    "label": self.graph.nodes[node].get("label", node),
                    "type": self.graph.nodes[node].get("type", "unknown")
                })
            
            hierarchies[root] = hierarchy
        
        return {
            "root_nodes": [{
                "id": root,
                "label": self.graph.nodes[root].get("label", root),
                "type": self.graph.nodes[root].get("type", "unknown"),
                "max_depth": max_depths[root]
            } for root in root_nodes],
            "hierarchies": hierarchies
        }
    
    def get_concept_evolution(self) -> List[Dict]:
        """
        Trace the evolution of concepts based on 'evolved_into' relationships
        
        Returns:
            List of concept evolution chains
        """
        evolution_chains = []
        visited = set()
        
        # Find all evolution relationships
        for source, target, data in self.graph.edges(data=True):
            relationship = data.get("label", "").lower()
            
            if "evolved" in relationship or "evolved_into" == relationship:
                if source not in visited:
                    # Start a new chain
                    chain = self._trace_evolution_chain(source)
                    evolution_chains.append(chain)
                    
                    # Mark all nodes in this chain as visited
                    for node in chain:
                        visited.add(node["id"])
        
        return evolution_chains
    
    def _trace_evolution_chain(self, start_node: str) -> List[Dict]:
        """Helper method to trace an evolution chain starting from a node"""
        chain = [{
            "id": start_node,
            "label": self.graph.nodes[start_node].get("label", start_node),
            "type": self.graph.nodes[start_node].get("type", "unknown")
        }]
        
        current = start_node
        while True:
            # Find evolution target
            found_next = False
            
            for _, target, data in self.graph.out_edges(current, data=True):
                relationship = data.get("label", "").lower()
                
                if "evolved" in relationship or "evolved_into" == relationship:
                    chain.append({
                        "id": target,
                        "label": self.graph.nodes[target].get("label", target),
                        "type": self.graph.nodes[target].get("type", "unknown")
                    })
                    current = target
                    found_next = True
                    break
            
            if not found_next:
                break
        
        return chain
    
    def get_related_concepts(self, concept_id: str, relationship_types: Optional[List[str]] = None) -> Dict:
        """
        Get concepts related to the given concept, optionally filtered by relationship types
        
        Args:
            concept_id: ID of the concept
            relationship_types: Optional list of relationship types to filter by
            
        Returns:
            Dictionary of related concepts grouped by relationship type
        """
        if concept_id not in self.graph:
            return {"error": f"Concept '{concept_id}' not found"}
        
        related = {}
        
        # Outgoing relationships
        for _, target, data in self.graph.out_edges(concept_id, data=True):
            relationship = data.get("label", "related")
            
            if relationship_types and relationship not in relationship_types:
                continue
                
            if relationship not in related:
                related[relationship] = []
                
            related[relationship].append({
                "id": target,
                "label": self.graph.nodes[target].get("label", target),
                "type": self.graph.nodes[target].get("type", "unknown"),
                "direction": "outgoing"
            })
        
        # Incoming relationships
        for source, _, data in self.graph.in_edges(concept_id, data=True):
            relationship = data.get("label", "related")
            
            if relationship_types and relationship not in relationship_types:
                continue
                
            # Create an "inverse" relationship name
            inverse_relationship = f"inverse_{relationship}"
            
            if inverse_relationship not in related:
                related[inverse_relationship] = []
                
            related[inverse_relationship].append({
                "id": source,
                "label": self.graph.nodes[source].get("label", source),
                "type": self.graph.nodes[source].get("type", "unknown"),
                "direction": "incoming"
            })
        
        return related
    
    def get_relationship_types(self) -> Dict[str, int]:
        """
        Get a count of edges by relationship type
        
        Returns:
            Dictionary mapping relationship type to count
        """
        relationship_counts = {}
        
        for _, _, data in self.graph.edges(data=True):
            relationship = data.get("label", "unknown")
            
            if relationship not in relationship_counts:
                relationship_counts[relationship] = 0
            relationship_counts[relationship] += 1
        
        return relationship_counts

    def generate_ontology_summary(self) -> Dict:
        """
        Generate a summary of the ontology
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "entity_types": self.get_entity_types(),
            "relationship_types": self.get_relationship_types(),
            "central_entities": self.get_central_entities(5),
            "sections": len(self.structured_ontology),
            "subsections": sum(
                len(section.get("subsections", {}))
                for section in self.structured_ontology.values()
            )
        }