import networkx as nx
import json
import datetime
import uuid
import re
from typing import List, Dict, Any, Optional, Set, Tuple

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
        self.data_source = data_source
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
            # Create node attributes dictionary with all node properties
            node_attrs = {
                "label": node.get("label", node["id"]),
                "type": node.get("type", "unknown")
            }
            
            # Add external_url if present
            if "external_url" in node:
                node_attrs["external_url"] = node["external_url"]
            
            self.graph.add_node(
                node["id"],
                **node_attrs
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
                depth_str = str(depth)  # Convert to string key for JSON serialization
                if depth_str not in hierarchy:
                    hierarchy[depth_str] = []
                hierarchy[depth_str].append({
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
        
    def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity in the graph
        
        Args:
            entity_data: Dictionary with entity data
            
        Returns:
            Dictionary with created entity data
            
        Raises:
            ValueError: If entity creation fails
        """
        # Generate an ID if not provided
        entity_id = entity_data.get('id')
        if not entity_id:
            # Generate an ID from the label if possible
            if 'label' in entity_data:
                # Convert label to a safe ID format (lowercase, underscores)
                entity_id = re.sub(r'[^a-z0-9_]', '_', entity_data['label'].lower()).strip('_')
                
                # If ID already exists, append a unique suffix
                if entity_id in self.graph:
                    entity_id = f"{entity_id}_{str(uuid.uuid4())[:8]}"
            else:
                # Generate a random ID
                entity_id = str(uuid.uuid4())
        
        # Check if entity ID already exists
        if entity_id in self.graph:
            raise ValueError(f"Entity with ID '{entity_id}' already exists")
        
        # Create node attributes
        node_attrs = {
            "label": entity_data.get('label', entity_id),
            "type": entity_data.get('type', 'unknown'),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        # Add optional attributes
        if 'description' in entity_data:
            node_attrs['description'] = entity_data['description']
        
        if 'external_url' in entity_data:
            node_attrs['external_url'] = entity_data['external_url']
        
        if 'attributes' in entity_data and isinstance(entity_data['attributes'], dict):
            # Merge custom attributes
            for key, value in entity_data['attributes'].items():
                if key not in node_attrs:
                    node_attrs[key] = value
        
        # Add the node to the graph
        self.graph.add_node(entity_id, **node_attrs)
        
        # Get the node attributes from the graph
        attributes = self.graph.nodes[entity_id]
        
        # Format the response
        entity = {
            "id": entity_id,
            "attributes": attributes,
            "incoming": [],
            "outgoing": []
        }
        
        return entity
    
    def update_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing entity
        
        Args:
            entity_id: ID of the entity to update
            entity_data: Dictionary with fields to update
            
        Returns:
            Dictionary with updated entity data, or None if entity not found
            
        Raises:
            ValueError: If update data is invalid
        """
        # Check if entity exists
        if entity_id not in self.graph:
            return None
        
        # Get current attributes
        node_attrs = dict(self.graph.nodes[entity_id])
        
        # Update the node
        if 'label' in entity_data:
            node_attrs['label'] = entity_data['label']
        
        if 'type' in entity_data:
            node_attrs['type'] = entity_data['type']
        
        if 'description' in entity_data:
            node_attrs['description'] = entity_data['description']
        
        if 'external_url' in entity_data:
            node_attrs['external_url'] = entity_data['external_url']
        
        if 'attributes' in entity_data and isinstance(entity_data['attributes'], dict):
            # Merge custom attributes
            for key, value in entity_data['attributes'].items():
                if key not in ('label', 'type', 'description', 'external_url', 'created_at'):
                    node_attrs[key] = value
        
        # Add updated timestamp
        node_attrs['updated_at'] = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Update the node attributes
        for key, value in node_attrs.items():
            self.graph.nodes[entity_id][key] = value
        
        # Format the response
        entity = {
            "id": entity_id,
            "attributes": node_attrs
        }
        
        return entity
    
    def delete_entity(self, entity_id: str, cascade: bool = False) -> Dict[str, Any]:
        """
        Delete an entity and optionally its relationships
        
        Args:
            entity_id: ID of the entity to delete
            cascade: Whether to cascade delete relationships
            
        Returns:
            Dictionary with deletion result
        """
        # Check if entity exists
        if entity_id not in self.graph:
            return {"success": False, "not_found": True}
        
        # Check if entity has relationships
        has_relationships = False
        for _, _, _ in self.graph.in_edges(entity_id, data=True):
            has_relationships = True
            break
        
        if not has_relationships:
            for _, _, _ in self.graph.out_edges(entity_id, data=True):
                has_relationships = True
                break
        
        # Check if we can delete the entity
        if has_relationships and not cascade:
            return {
                "success": False, 
                "message": "Entity has relationships. Use cascade=true to delete them."
            }
        
        # Delete related relationships
        relationships_removed = 0
        if cascade:
            # Delete incoming relationships
            for source, _ in list(self.graph.in_edges(entity_id)):
                self.graph.remove_edge(source, entity_id)
                relationships_removed += 1
            
            # Delete outgoing relationships
            for _, target in list(self.graph.out_edges(entity_id)):
                self.graph.remove_edge(entity_id, target)
                relationships_removed += 1
        
        # Delete the entity
        self.graph.remove_node(entity_id)
        
        return {
            "success": True,
            "relationships_removed": relationships_removed
        }
    
    def create_relationship(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new relationship between entities
        
        Args:
            relationship_data: Dictionary with relationship data
            
        Returns:
            Dictionary with created relationship data
            
        Raises:
            ValueError: If relationship creation fails
        """
        source_id = relationship_data.get('source_id')
        target_id = relationship_data.get('target_id')
        rel_type = relationship_data.get('relationship_type')
        
        # Check if source and target exist
        if source_id not in self.graph:
            raise ValueError(f"Source entity '{source_id}' not found")
        
        if target_id not in self.graph:
            raise ValueError(f"Target entity '{target_id}' not found")
        
        # Check if relationship already exists
        if self.graph.has_edge(source_id, target_id):
            # If a relationship of the same type exists, raise an error
            for _, _, data in self.graph.out_edges(source_id, data=True):
                if data.get('label') == rel_type:
                    raise ValueError(f"Relationship of type '{rel_type}' already exists between entities")
        
        # Generate relationship ID
        relationship_id = str(uuid.uuid4())
        
        # Create edge attributes
        edge_attrs = {
            "id": relationship_id,
            "label": rel_type,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        # Add custom attributes
        if 'attributes' in relationship_data and isinstance(relationship_data['attributes'], dict):
            for key, value in relationship_data['attributes'].items():
                if key not in edge_attrs:
                    edge_attrs[key] = value
        
        # Add the edge to the graph
        self.graph.add_edge(source_id, target_id, **edge_attrs)
        
        # Format the response
        source_label = self.graph.nodes[source_id].get('label', source_id)
        target_label = self.graph.nodes[target_id].get('label', target_id)
        
        relationship = {
            "id": relationship_id,
            "source_id": source_id,
            "source_label": source_label,
            "target_id": target_id,
            "target_label": target_label,
            "relationship_type": rel_type,
            "attributes": {k: v for k, v in edge_attrs.items() if k not in ('id', 'label', 'created_at')},
            "created_at": edge_attrs["created_at"]
        }
        
        return relationship
    
    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by ID
        
        Args:
            relationship_id: ID of the relationship to get
            
        Returns:
            Dictionary with relationship data, or None if not found
        """
        # Find the relationship by ID
        for source, target, data in self.graph.edges(data=True):
            if data.get('id') == relationship_id:
                source_label = self.graph.nodes[source].get('label', source)
                source_type = self.graph.nodes[source].get('type', 'unknown')
                target_label = self.graph.nodes[target].get('label', target)
                target_type = self.graph.nodes[target].get('type', 'unknown')
                
                return {
                    "id": relationship_id,
                    "source_id": source,
                    "source_label": source_label,
                    "source_type": source_type,
                    "target_id": target,
                    "target_label": target_label,
                    "target_type": target_type,
                    "relationship_type": data.get('label', 'related_to'),
                    "attributes": {k: v for k, v in data.items() if k not in ('id', 'label', 'created_at', 'updated_at')},
                    "created_at": data.get('created_at'),
                    "updated_at": data.get('updated_at')
                }
        
        return None
    
    def update_relationship(self, relationship_id: str, relationship_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing relationship
        
        Args:
            relationship_id: ID of the relationship to update
            relationship_data: Dictionary with fields to update
            
        Returns:
            Dictionary with updated relationship data, or None if not found
            
        Raises:
            ValueError: If update data is invalid
        """
        # Find the relationship by ID
        for source, target, data in self.graph.edges(data=True):
            if data.get('id') == relationship_id:
                # Update the edge data
                if 'relationship_type' in relationship_data:
                    self.graph[source][target]['label'] = relationship_data['relationship_type']
                
                if 'attributes' in relationship_data and isinstance(relationship_data['attributes'], dict):
                    # Merge custom attributes
                    for key, value in relationship_data['attributes'].items():
                        if key not in ('id', 'label', 'created_at'):
                            self.graph[source][target][key] = value
                
                # Add updated timestamp
                self.graph[source][target]['updated_at'] = datetime.datetime.utcnow().isoformat() + "Z"
                
                # Get the updated data
                updated_data = dict(self.graph[source][target])
                
                source_label = self.graph.nodes[source].get('label', source)
                target_label = self.graph.nodes[target].get('label', target)
                
                return {
                    "id": relationship_id,
                    "source_id": source,
                    "target_id": target,
                    "relationship_type": updated_data.get('label', 'related_to'),
                    "attributes": {k: v for k, v in updated_data.items() if k not in ('id', 'label', 'created_at', 'updated_at')},
                    "updated_at": updated_data.get('updated_at')
                }
        
        return None
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship
        
        Args:
            relationship_id: ID of the relationship to delete
            
        Returns:
            Boolean indicating success
        """
        # Find the relationship by ID
        for source, target, data in list(self.graph.edges(data=True)):
            if data.get('id') == relationship_id:
                # Remove the edge
                self.graph.remove_edge(source, target)
                return True
        
        return False
    
    def list_entities(self, entity_type: Optional[str] = None, query: Optional[str] = None, 
                      limit: int = 50, offset: int = 0, sort: str = 'created_at', 
                      order: str = 'desc') -> Dict[str, Any]:
        """
        List entities with optional filtering
        
        Args:
            entity_type: Optional entity type to filter by
            query: Optional search term for labels and descriptions
            limit: Maximum number of results to return
            offset: Pagination offset
            sort: Field to sort by
            order: Sort order - 'asc' or 'desc'
            
        Returns:
            Dictionary with list of entities and total count
        """
        # Get all entities
        entities = []
        for node_id, attrs in self.graph.nodes(data=True):
            # Skip if entity type doesn't match
            if entity_type and attrs.get('type') != entity_type:
                continue
            
            # Skip if query doesn't match
            if query:
                label = attrs.get('label', '').lower()
                description = attrs.get('description', '').lower()
                query_lower = query.lower()
                
                if query_lower not in label and query_lower not in description:
                    continue
            
            # Add entity to results
            entities.append({
                "id": node_id,
                "label": attrs.get('label', node_id),
                "type": attrs.get('type', 'unknown'),
                "description": attrs.get('description', ''),
                "created_at": attrs.get('created_at')
            })
        
        # Sort entities
        reverse = order.lower() == 'desc'
        
        if sort == 'label':
            entities.sort(key=lambda e: e.get('label', ''), reverse=reverse)
        elif sort == 'type':
            entities.sort(key=lambda e: e.get('type', ''), reverse=reverse)
        elif sort == 'created_at':
            entities.sort(key=lambda e: e.get('created_at', ''), reverse=reverse)
        else:
            # Default to sorting by ID
            entities.sort(key=lambda e: e.get('id', ''), reverse=reverse)
        
        # Apply pagination
        total = len(entities)
        entities = entities[offset:offset + limit]
        
        return {
            "entities": entities,
            "total": total
        }
    
    def list_relationships(self, source_id: Optional[str] = None, target_id: Optional[str] = None, 
                           entity_id: Optional[str] = None, relationship_type: Optional[str] = None, 
                           limit: int = 50, offset: int = 0, sort: str = 'created_at', 
                           order: str = 'desc') -> Dict[str, Any]:
        """
        List relationships with optional filtering
        
        Args:
            source_id: Optional source entity ID to filter by
            target_id: Optional target entity ID to filter by
            entity_id: Optional entity ID to filter by (either source or target)
            relationship_type: Optional relationship type to filter by
            limit: Maximum number of results to return
            offset: Pagination offset
            sort: Field to sort by
            order: Sort order - 'asc' or 'desc'
            
        Returns:
            Dictionary with list of relationships and total count
        """
        # Get all relationships
        relationships = []
        for source, target, data in self.graph.edges(data=True):
            # Skip if source doesn't match
            if source_id and source != source_id:
                continue
            
            # Skip if target doesn't match
            if target_id and target != target_id:
                continue
            
            # Skip if entity doesn't match
            if entity_id and source != entity_id and target != entity_id:
                continue
            
            # Skip if relationship type doesn't match
            rel_type = data.get('label', 'related_to')
            if relationship_type and rel_type != relationship_type:
                continue
            
            # Add relationship to results
            source_label = self.graph.nodes[source].get('label', source)
            target_label = self.graph.nodes[target].get('label', target)
            
            relationships.append({
                "id": data.get('id', f"{source}_{target}"),
                "source_id": source,
                "source_label": source_label,
                "target_id": target,
                "target_label": target_label,
                "relationship_type": rel_type,
                "created_at": data.get('created_at')
            })
        
        # Sort relationships
        reverse = order.lower() == 'desc'
        
        if sort == 'relationship_type':
            relationships.sort(key=lambda r: r.get('relationship_type', ''), reverse=reverse)
        elif sort == 'source_label':
            relationships.sort(key=lambda r: r.get('source_label', ''), reverse=reverse)
        elif sort == 'target_label':
            relationships.sort(key=lambda r: r.get('target_label', ''), reverse=reverse)
        elif sort == 'created_at':
            relationships.sort(key=lambda r: r.get('created_at', ''), reverse=reverse)
        else:
            # Default to sorting by ID
            relationships.sort(key=lambda r: r.get('id', ''), reverse=reverse)
        
        # Apply pagination
        total = len(relationships)
        relationships = relationships[offset:offset + limit]
        
        return {
            "relationships": relationships,
            "total": total
        }
        
    def save_changes(self) -> bool:
        """
        Save changes to the knowledge graph to disk
        
        Returns:
            Boolean indicating success
        """
        try:
            # Convert NetworkX graph to knowledge graph format
            nodes = []
            for node_id, attrs in self.graph.nodes(data=True):
                node = {"id": node_id}
                for key, value in attrs.items():
                    node[key] = value
                nodes.append(node)
            
            edges = []
            for source, target, data in self.graph.edges(data=True):
                edge = {
                    "source": source,
                    "target": target
                }
                for key, value in data.items():
                    edge[key] = value
                edges.append(edge)
            
            # Create updated knowledge graph data
            updated_knowledge_graph = {
                "nodes": nodes,
                "edges": edges
            }
            
            # Update the data
            self.data["knowledge_graph"] = updated_knowledge_graph
            
            # Save to file if data source is a file path
            if isinstance(self.data_source, str):
                with open(self.data_source, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving changes: {e}")
            return False