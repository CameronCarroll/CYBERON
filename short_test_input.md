# Biology

- Entity: Homo sapiens
  Description: The human species.
  Type: Species
  Attributes:
    - Attribute: Average Lifespan
      Value: 79 years
    - Attribute: Genome Size [url:/genomes/homo_sapiens]
      Value: 3.2 billion base pairs
  Relationships:
    - Relationship: evolved_from
      Target: Homo erectus
    - Relationship: closely_related_to
      Target: Pan troglodytes

- Entity: Homo erectus
  Description: An extinct species of archaic humans.
  Type: Species
  Attributes:
    - Attribute: Average Brain Size
      Value: 900 cm³

- Entity: Pan troglodytes
  Description: The common chimpanzee.
  Type: Species
  Attributes:
    - Attribute: Average Lifespan
      Value: 40 years
    - Attribute: Social Structure
      Value: Fission-fusion communities

# Anatomy

- Entity: Heart
  Description: A muscular organ that pumps blood through the circulatory system.
  Type: Organ
  Attributes:
    - Attribute: Chambers
      Value: 4
    - Attribute: Function
      Value: Circulate blood
  Relationships:
    - Relationship: located_in
      Target: Thoracic cavity

- Entity: Thoracic cavity
  Description: The chamber of the body of vertebrates that is protected by the thoracic wall.
  Type: BodyRegion

# Philosophy

- Entity: Plato
  Description: A philosopher in Classical Greece.
  Type: Person
  Attributes:
    - Attribute: Known For
      Value: Theory of Forms
    - Attribute: Era
      Value: Classical Greek
  Relationships:
    - Relationship: teacher_of
      Target: Aristotle

- Entity: Aristotle
  Description: Greek philosopher and polymath during the Classical period in Ancient Greece.
  Type: Person
