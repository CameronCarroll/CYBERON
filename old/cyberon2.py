from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Union
from enum import Enum
import json
from datetime import datetime

class OntologyType(Enum):
    CONCEPT = "concept"
    PERSON = "person"
    THEORY = "theory"
    PRINCIPLE = "principle"
    DOMAIN = "domain"
    APPLICATION = "application"
    TECHNOLOGY = "technology"

class RelationshipType(Enum):
    DEVELOPED_BY = "developed_by"
    INFLUENCED = "influenced"
    PART_OF = "part_of"
    EVOLVED_INTO = "evolved_into"
    APPLIED_IN = "applied_in"
    DERIVED_FROM = "derived_from"
    COMPARABLE_TO = "comparable_to"
    CONTRADICTS = "contradicts"

@dataclass
class TimeFrame:
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    period_name: Optional[str] = None
    
    def __str__(self):
        if self.period_name:
            return self.period_name
        if self.start_year and self.end_year:
            return f"{self.start_year}-{self.end_year}"
        if self.start_year:
            return f"{self.start_year}-present"
        return "unknown timeframe"

@dataclass
class Relationship:
    target_id: str
    relationship_type: RelationshipType
    description: Optional[str] = None
    strength: int = 1  # 1-10 scale for connection strength

@dataclass
class OntologyEntity:
    id: str
    name: str
    entity_type: OntologyType
    description: str = ""
    relationships: List[Relationship] = field(default_factory=list)
    timeframe: Optional[TimeFrame] = None
    tags: Set[str] = field(default_factory=set)
    references: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_relationship(self, target_id: str, rel_type: RelationshipType, 
                         description: str = None, strength: int = 1):
        """Add a relationship to another entity"""
        self.relationships.append(
            Relationship(target_id=target_id, 
                        relationship_type=rel_type,
                        description=description,
                        strength=strength)
        )
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type.value,
            "description": self.description,
            "relationships": [
                {
                    "target": r.target_id,
                    "type": r.relationship_type.value,
                    "description": r.description,
                    "strength": r.strength
                } for r in self.relationships
            ],
            "timeframe": {
                "start_year": self.timeframe.start_year if self.timeframe else None,
                "end_year": self.timeframe.end_year if self.timeframe else None,
                "period_name": self.timeframe.period_name if self.timeframe else None
            } if self.timeframe else None,
            "tags": list(self.tags),
            "references": self.references,
            "metadata": self.metadata
        }

@dataclass
class Person(OntologyEntity):
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    contributions: List[str] = field(default_factory=list)
    institutions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.entity_type != OntologyType.PERSON:
            self.entity_type = OntologyType.PERSON

    def to_dict(self):
        person_dict = super().to_dict()
        person_dict.update({
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "contributions": self.contributions,
            "institutions": self.institutions
        })
        return person_dict

@dataclass
class Concept(OntologyEntity):
    related_concepts: List[str] = field(default_factory=list)
    formalized_by: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.entity_type != OntologyType.CONCEPT:
            self.entity_type = OntologyType.CONCEPT
    
    def to_dict(self):
        concept_dict = super().to_dict()
        concept_dict.update({
            "related_concepts": self.related_concepts,
            "formalized_by": self.formalized_by
        })
        return concept_dict

class CyberneticsOntology:
    def __init__(self):
        self.entities: Dict[str, OntologyEntity] = {}
        self.created_at = datetime.now()
        self.last_updated = self.created_at
    
    def add_entity(self, entity: OntologyEntity):
        """Add an entity to the ontology"""
        self.entities[entity.id] = entity
        self.last_updated = datetime.now()
    
    def get_entity(self, entity_id: str) -> Optional[OntologyEntity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: OntologyType) -> List[OntologyEntity]:
        """Get all entities of a specific type"""
        return [e for e in self.entities.values() if e.entity_type == entity_type]
    
    def get_entities_by_tag(self, tag: str) -> List[OntologyEntity]:
        """Get all entities with a specific tag"""
        return [e for e in self.entities.values() if tag in e.tags]
    
    def get_related_entities(self, entity_id: str) -> Dict[str, List[Relationship]]:
        """Get all entities related to the given entity"""
        if entity_id not in self.entities:
            return {}
        
        related = {}
        entity = self.entities[entity_id]
        
        # Direct relationships from this entity
        for rel in entity.relationships:
            if rel.target_id in self.entities:
                if rel.target_id not in related:
                    related[rel.target_id] = []
                related[rel.target_id].append(rel)
        
        # Relationships to this entity
        for eid, e in self.entities.items():
            if eid == entity_id:
                continue
                
            for rel in e.relationships:
                if rel.target_id == entity_id:
                    if eid not in related:
                        related[eid] = []
                    # Create an inverse relationship object
                    inverse_rel = Relationship(
                        target_id=eid,
                        relationship_type=rel.relationship_type,
                        description=f"Inverse: {rel.description}" if rel.description else None,
                        strength=rel.strength
                    )
                    related[eid].append(inverse_rel)
        
        return related
    
    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths between two entities up to a maximum depth"""
        if start_id not in self.entities or end_id not in self.entities:
            return []
            
        def dfs(current_id, target_id, path, visited, paths, depth):
            if depth > max_depth:
                return
                
            if current_id == target_id:
                paths.append(path.copy())
                return
                
            visited.add(current_id)
            
            entity = self.entities[current_id]
            for rel in entity.relationships:
                next_id = rel.target_id
                if next_id not in visited and next_id in self.entities:
                    path.append(next_id)
                    dfs(next_id, target_id, path, visited, paths, depth + 1)
                    path.pop()
                    
            visited.remove(current_id)
        
        paths = []
        dfs(start_id, end_id, [start_id], set(), paths, 0)
        return paths
    
    def to_json(self, filename: Optional[str] = None) -> str:
        """Export the ontology to JSON"""
        data = {
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat(),
                "entity_count": len(self.entities)
            },
            "entities": {eid: entity.to_dict() for eid, entity in self.entities.items()}
        }
        
        json_str = json.dumps(data, indent=2)
        if filename:
            with open(filename, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    @classmethod
    def from_json(cls, json_data: Union[str, Dict]) -> 'CyberneticsOntology':
        """Create an ontology from JSON data"""
        if isinstance(json_data, str):
            try:
                with open(json_data, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = json.loads(json_data)
        else:
            data = json_data
            
        ontology = cls()
        
        for eid, entity_data in data.get("entities", {}).items():
            entity_type = entity_data.get("type")
            
            if entity_type == OntologyType.PERSON.value:
                entity = Person(
                    id=entity_data.get("id"),
                    name=entity_data.get("name"),
                    entity_type=OntologyType.PERSON,
                    description=entity_data.get("description", ""),
                    birth_year=entity_data.get("birth_year"),
                    death_year=entity_data.get("death_year"),
                    contributions=entity_data.get("contributions", []),
                    institutions=entity_data.get("institutions", [])
                )
            elif entity_type == OntologyType.CONCEPT.value:
                entity = Concept(
                    id=entity_data.get("id"),
                    name=entity_data.get("name"),
                    entity_type=OntologyType.CONCEPT,
                    description=entity_data.get("description", ""),
                    related_concepts=entity_data.get("related_concepts", []),
                    formalized_by=entity_data.get("formalized_by", [])
                )
            else:
                entity = OntologyEntity(
                    id=entity_data.get("id"),
                    name=entity_data.get("name"),
                    entity_type=OntologyType(entity_data.get("type")),
                    description=entity_data.get("description", "")
                )
            
            # Add timeframe if exists
            if entity_data.get("timeframe"):
                tf = entity_data["timeframe"]
                entity.timeframe = TimeFrame(
                    start_year=tf.get("start_year"),
                    end_year=tf.get("end_year"),
                    period_name=tf.get("period_name")
                )
            
            # Add tags
            entity.tags = set(entity_data.get("tags", []))
            
            # Add references
            entity.references = entity_data.get("references", [])
            
            # Add metadata
            entity.metadata = entity_data.get("metadata", {})
            
            # Add relationships
            for rel_data in entity_data.get("relationships", []):
                entity.add_relationship(
                    target_id=rel_data.get("target"),
                    rel_type=RelationshipType(rel_data.get("type")),
                    description=rel_data.get("description"),
                    strength=rel_data.get("strength", 1)
                )
            
            ontology.add_entity(entity)
        
        return ontology

# Example usage
def create_sample_ontology():
    """Create a sample cybernetics ontology"""
    ontology = CyberneticsOntology()
    
    # Add people
    wiener = Person(
        id="wiener",
        name="Norbert Wiener",
        entity_type=OntologyType.PERSON,
        description="Mathematician who coined the term 'cybernetics'",
        birth_year=1894,
        death_year=1964,
        contributions=["Feedback theory", "Cybernetics founding", "Information theory"],
        institutions=["MIT"]
    )
    wiener.tags = {"first_order", "information_theory", "founding_figure"}
    
    ashby = Person(
        id="ashby",
        name="W. Ross Ashby",
        entity_type=OntologyType.PERSON,
        description="Pioneer in systems theory and cybernetics",
        birth_year=1903,
        death_year=1972,
        contributions=["Law of requisite variety", "Homeostasis", "Design for a Brain"],
        institutions=["Barnwood House Hospital", "University of Illinois"]
    )
    ashby.tags = {"first_order", "systems_theory", "founding_figure"}
    
    # Add concepts
    cybernetics = Concept(
        id="cybernetics",
        name="Cybernetics",
        entity_type=OntologyType.CONCEPT,
        description="The science of control and communication in the animal and the machine",
        formalized_by=["wiener"],
        timeframe=TimeFrame(start_year=1948, period_name="Modern era")
    )
    cybernetics.tags = {"core_concept", "interdisciplinary"}
    
    feedback = Concept(
        id="feedback",
        name="Feedback Loops",
        entity_type=OntologyType.CONCEPT,
        description="Circular processes where outputs are fed back as inputs",
        formalized_by=["wiener"],
        related_concepts=["homeostasis", "control_theory"]
    )
    feedback.tags = {"core_principle", "universal_mechanism"}
    
    # Create relationships
    wiener.add_relationship("cybernetics", RelationshipType.DEVELOPED_BY, 
                           "Coined term in his 1948 book", 10)
    wiener.add_relationship("feedback", RelationshipType.DEVELOPED_BY, 
                           "Formalized feedback theory", 9)
    
    ashby.add_relationship("cybernetics", RelationshipType.INFLUENCED, 
                          "Expanded theoretical foundations", 8)
    
    cybernetics.add_relationship("feedback", RelationshipType.PART_OF, 
                               "Fundamental concept in cybernetics", 10)
    
    # Add entities to ontology
    ontology.add_entity(wiener)
    ontology.add_entity(ashby)
    ontology.add_entity(cybernetics)
    ontology.add_entity(feedback)
    
    return ontology

if __name__ == "__main__":
    # Create a sample ontology
    ontology = create_sample_ontology()
    
    # Export to JSON
    ontology.to_json("cybernetics_ontology.json")
    
    # Query examples
    print("\nPeople in the ontology:")
    for person in ontology.get_entities_by_type(OntologyType.PERSON):
        print(f"- {person.name} ({person.birth_year}-{person.death_year})")
        print(f"  Contributions: {', '.join(person.contributions)}")
    
    print("\nConcepts related to Cybernetics:")
    related = ontology.get_related_entities("cybernetics")
    for entity_id, relationships in related.items():
        entity = ontology.get_entity(entity_id)
        for rel in relationships:
            print(f"- {entity.name}: {rel.relationship_type.value} " + 
                  f"(strength: {rel.strength})" +
                  (f" - {rel.description}" if rel.description else ""))