# Technology

## Software

- Entity: Linux Kernel
  Description: An open-source, monolithic, Unix-like operating system kernel.
  Type: OS Kernel
  Attributes:
    - Attribute: Primary Author [url:/people/linus_torvalds]
      Value: Linus Torvalds
    - Attribute: Written In
      Value: C, Assembly
    - Attribute: License
      Value: GPLv2
  Relationships:
    - Relationship: influenced_by
      Target: Unix
    - Relationship: commonly_used_with
      Target: GNU Tools

- Entity: Unix
  Description: A family of multitasking, multi-user computer operating systems.
  Type: Operating System Family
  Attributes:
    - Attribute: Origin
      Value: Bell Labs
    - Attribute: Key Concepts
      Value: Hierarchical filesystem, Everything is a file

## Hardware

- Entity: CPU
  Description: Central Processing Unit; the primary component executing instructions.
  Type: Hardware Component
  Attributes:
    - Attribute: Function
      Value: Computation and Control
    - Attribute: Key Metrics
      Value: Clock Speed, Core Count, IPC
  Relationships:
    - Relationship: connects_to
      Target: Motherboard
    - Relationship: executes
      Target: Software Instructions

- Entity: Motherboard
  Description: The main printed circuit board (PCB) connecting crucial components.
  Type: Hardware Component
  Attributes:
    - Attribute: Holds Components Like
      Value: CPU, RAM, Expansion Slots
  Relationships:
    - Relationship: provides_interface_for
      Target: CPU

# Foundational Concepts

## Physics

- Entity: General Relativity
  Description: Einstein's geometric theory of gravitation.
  Type: Physical Theory
  Attributes:
    - Attribute: Author [url:/people/albert_einstein]
      Value: Albert Einstein
    - Attribute: Describes
      Value: Gravity as spacetime curvature
  Relationships:
    - Relationship: explains
      Target: Gravity
    - Relationship: successor_to
      Target: Newtonian Gravity

- Entity: Gravity
  Description: Fundamental interaction causing mutual attraction between things with mass or energy.
  Type: Fundamental Force
  Attributes:
    - Attribute: Mediated By (Theoretical)
      Value: Graviton

## Computing Concepts (Placeholder Category)

- Entity: Software Instructions
  Description: Commands executed by a CPU.
  Type: Concept

- Entity: GNU Tools
  Description: Core utilities often bundled with the Linux kernel to form a full OS.
  Type: Software Collection

- Entity: Newtonian Gravity
  Description: Classical mechanics description of gravitational attraction.
  Type: Physical Theory