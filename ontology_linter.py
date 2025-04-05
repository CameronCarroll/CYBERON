import re

def lint_ontology(path):
    issues = []
    with open(path, 'r') as f:
        lines = f.readlines()

    current_entity = None
    expecting_value = False
    expecting_target = False
    defined_entities = set()
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if stripped.startswith("- Entity:"):
            current_entity = stripped.split(": ", 1)[-1].strip()
            defined_entities.add(current_entity)
            expecting_value = expecting_target = False
        
        elif stripped.startswith("- Attribute:"):
            expecting_value = True
            expecting_target = False
        
        elif stripped.startswith("Value:"):
            if not expecting_value:
                issues.append(f"Line {i+1}: 'Value:' found without matching '- Attribute:'")
            expecting_value = False
        
        elif stripped.startswith("- Relationship:"):
            expecting_target = True
            expecting_value = False
        
        elif stripped.startswith("Target:"):
            if not expecting_target:
                issues.append(f"Line {i+1}: 'Target:' found without matching '- Relationship:'")
            else:
                target_entity = stripped.split(": ", 1)[-1].strip()
                if target_entity not in defined_entities:
                    issues.append(f"Line {i+1}: Target '{target_entity}' not defined as an entity")
            expecting_target = False
        
        elif stripped.startswith("Value:") or stripped.startswith("Target:"):
            # Catch stray Value/Target
            if not (expecting_value or expecting_target):
                issues.append(f"Line {i+1}: Unexpected '{stripped}'")
    
    if expecting_value:
        issues.append("File ended while expecting a 'Value:' for an attribute.")
    if expecting_target:
        issues.append("File ended while expecting a 'Target:' for a relationship.")

    return issues

# Usage
issues = lint_ontology("test_input.md")
for issue in issues:
    print(issue)
