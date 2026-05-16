#!/bin/bash
set -e

# Ensure the workspace directory exists
mkdir -p /workspace

# Create the ontology_mapper skill module directly in the workspace
# (since the skill code is the library itself, we materialize it as a module)
cat > /workspace/ontology_mapper.py << 'PYEOF'
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import json
import re

class OntologyType(Enum):
    """Standard construction ontologies"""
    IFC = "ifc"
    COBIE = "cobie"
    UNICLASS = "uniclass"
    OMNICLASS = "omniclass"
    MASTERFORMAT = "masterformat"
    UNIFORMAT = "uniformat"
    CUSTOM = "custom"

class MappingConfidence(Enum):
    """Confidence level of mapping"""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

class RelationType(Enum):
    """Types of relationships between concepts"""
    EQUIVALENT = "equivalent"
    BROADER = "broader"
    NARROWER = "narrower"
    RELATED = "related"
    PART_OF = "part_of"
    HAS_PART = "has_part"

@dataclass
class OntologyConcept:
    """Concept in an ontology"""
    id: str
    name: str
    ontology: OntologyType
    definition: Optional[str] = None
    parent_id: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)

@dataclass
class SemanticMapping:
    """Mapping between two concepts"""
    source_concept: str
    source_ontology: OntologyType
    target_concept: str
    target_ontology: OntologyType
    relation: RelationType
    confidence: MappingConfidence
    notes: Optional[str] = None
    created_by: str = "auto"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MappingResult:
    """Result of ontology mapping operation"""
    source_field: str
    source_value: str
    mappings: List[SemanticMapping]
    best_match: Optional[SemanticMapping] = None
    unmapped: bool = False

@dataclass
class OntologyMappingReport:
    """Complete mapping report"""
    total_fields: int
    mapped_fields: int
    unmapped_fields: int
    mappings: List[MappingResult]
    coverage: float
    confidence_distribution: Dict[str, int]
    recommendations: List[str]


class OntologyMapper:
    """
    Map construction data to standard ontologies.
    Based on DDC methodology Chapter 2.2.
    """

    def __init__(self):
        self.ontologies = self._load_ontologies()
        self.mapping_rules = self._load_mapping_rules()
        self.synonym_map = self._build_synonym_map()

    def _load_ontologies(self) -> Dict[OntologyType, Dict[str, OntologyConcept]]:
        ontologies = {}

        ontologies[OntologyType.IFC] = {
            "IfcWall": OntologyConcept("IfcWall", "Wall", OntologyType.IFC,
                "A vertical construction that bounds or subdivides spaces"),
            "IfcSlab": OntologyConcept("IfcSlab", "Slab", OntologyType.IFC,
                "A horizontal planar building element"),
            "IfcBeam": OntologyConcept("IfcBeam", "Beam", OntologyType.IFC,
                "A horizontal structural member"),
            "IfcColumn": OntologyConcept("IfcColumn", "Column", OntologyType.IFC,
                "A vertical structural member"),
            "IfcDoor": OntologyConcept("IfcDoor", "Door", OntologyType.IFC,
                "A building element for access"),
            "IfcWindow": OntologyConcept("IfcWindow", "Window", OntologyType.IFC,
                "A building element for light and ventilation"),
            "IfcRoof": OntologyConcept("IfcRoof", "Roof", OntologyType.IFC,
                "A building element covering a building"),
            "IfcStair": OntologyConcept("IfcStair", "Stair", OntologyType.IFC,
                "A vertical circulation element"),
            "IfcSpace": OntologyConcept("IfcSpace", "Space", OntologyType.IFC,
                "A defined volume of air"),
            "IfcBuildingStorey": OntologyConcept("IfcBuildingStorey", "Building Storey",
                OntologyType.IFC, "A horizontal aggregation of spaces"),
        }

        ontologies[OntologyType.COBIE] = {
            "Floor": OntologyConcept("Floor", "Floor", OntologyType.COBIE,
                "A floor or level in a building"),
            "Space": OntologyConcept("Space", "Space", OntologyType.COBIE,
                "A spatial region"),
            "Type": OntologyConcept("Type", "Type", OntologyType.COBIE,
                "A product type or specification"),
            "Component": OntologyConcept("Component", "Component", OntologyType.COBIE,
                "An individual product instance"),
            "Zone": OntologyConcept("Zone", "Zone", OntologyType.COBIE,
                "A spatial grouping of spaces"),
            "System": OntologyConcept("System", "System", OntologyType.COBIE,
                "A building system or network"),
        }

        ontologies[OntologyType.UNICLASS] = {
            "Ss_25": OntologyConcept("Ss_25", "Wall Systems", OntologyType.UNICLASS),
            "Ss_30": OntologyConcept("Ss_30", "Roof Systems", OntologyType.UNICLASS),
            "Ss_32": OntologyConcept("Ss_32", "Floor Systems", OntologyType.UNICLASS),
            "Ss_35": OntologyConcept("Ss_35", "Stair Systems", OntologyType.UNICLASS),
            "Pr_20": OntologyConcept("Pr_20", "Structural Products", OntologyType.UNICLASS),
            "Pr_30": OntologyConcept("Pr_30", "Wall Products", OntologyType.UNICLASS),
            "Pr_35": OntologyConcept("Pr_35", "Door Products", OntologyType.UNICLASS),
            "Pr_40": OntologyConcept("Pr_40", "Window Products", OntologyType.UNICLASS),
        }

        ontologies[OntologyType.MASTERFORMAT] = {
            "03": OntologyConcept("03", "Concrete", OntologyType.MASTERFORMAT),
            "04": OntologyConcept("04", "Masonry", OntologyType.MASTERFORMAT),
            "05": OntologyConcept("05", "Metals", OntologyType.MASTERFORMAT),
            "06": OntologyConcept("06", "Wood and Plastics", OntologyType.MASTERFORMAT),
            "07": OntologyConcept("07", "Thermal and Moisture Protection", OntologyType.MASTERFORMAT),
            "08": OntologyConcept("08", "Doors and Windows", OntologyType.MASTERFORMAT),
            "09": OntologyConcept("09", "Finishes", OntologyType.MASTERFORMAT),
            "22": OntologyConcept("22", "Plumbing", OntologyType.MASTERFORMAT),
            "23": OntologyConcept("23", "HVAC", OntologyType.MASTERFORMAT),
            "26": OntologyConcept("26", "Electrical", OntologyType.MASTERFORMAT),
        }

        return ontologies

    def _load_mapping_rules(self) -> List[SemanticMapping]:
        rules = [
            SemanticMapping("IfcBuildingStorey", OntologyType.IFC, "Floor",
                OntologyType.COBIE, RelationType.EQUIVALENT, MappingConfidence.EXACT),
            SemanticMapping("IfcSpace", OntologyType.IFC, "Space",
                OntologyType.COBIE, RelationType.EQUIVALENT, MappingConfidence.EXACT),
            SemanticMapping("IfcWall", OntologyType.IFC, "Ss_25",
                OntologyType.UNICLASS, RelationType.RELATED, MappingConfidence.HIGH),
            SemanticMapping("IfcRoof", OntologyType.IFC, "Ss_30",
                OntologyType.UNICLASS, RelationType.RELATED, MappingConfidence.HIGH),
            SemanticMapping("IfcSlab", OntologyType.IFC, "Ss_32",
                OntologyType.UNICLASS, RelationType.RELATED, MappingConfidence.HIGH),
            SemanticMapping("IfcDoor", OntologyType.IFC, "Pr_35",
                OntologyType.UNICLASS, RelationType.RELATED, MappingConfidence.HIGH),
            SemanticMapping("IfcWindow", OntologyType.IFC, "Pr_40",
                OntologyType.UNICLASS, RelationType.RELATED, MappingConfidence.HIGH),
            SemanticMapping("IfcDoor", OntologyType.IFC, "08",
                OntologyType.MASTERFORMAT, RelationType.BROADER, MappingConfidence.MEDIUM),
            SemanticMapping("IfcWindow", OntologyType.IFC, "08",
                OntologyType.MASTERFORMAT, RelationType.BROADER, MappingConfidence.MEDIUM),
        ]
        return rules

    def _build_synonym_map(self) -> Dict[str, List[str]]:
        return {
            "wall": ["partition", "barrier", "divider"],
            "door": ["entrance", "portal", "opening"],
            "window": ["glazing", "fenestration", "opening"],
            "floor": ["slab", "deck", "storey", "level"],
            "roof": ["roofing", "covering", "canopy"],
            "beam": ["girder", "joist", "lintel"],
            "column": ["pillar", "post", "pier"],
            "stair": ["stairway", "staircase", "steps"],
            "space": ["room", "area", "zone"],
            "concrete": ["cement", "reinforced"],
            "steel": ["metal", "iron"],
        }

    def map_field(
        self,
        field_name: str,
        field_value: str,
        source_ontology: Optional[OntologyType] = None,
        target_ontology: OntologyType = OntologyType.IFC
    ) -> MappingResult:
        mappings = []
        normalized = self._normalize_value(field_value)

        for rule in self.mapping_rules:
            if rule.target_ontology == target_ontology:
                if self._matches(normalized, rule.source_concept):
                    mappings.append(rule)

        target_concepts = self.ontologies.get(target_ontology, {})
        for concept_id, concept in target_concepts.items():
            similarity = self._calculate_similarity(normalized, concept)
            if similarity > 0.5:
                confidence = self._similarity_to_confidence(similarity)
                mappings.append(SemanticMapping(
                    source_concept=field_value,
                    source_ontology=source_ontology or OntologyType.CUSTOM,
                    target_concept=concept_id,
                    target_ontology=target_ontology,
                    relation=RelationType.EQUIVALENT if similarity > 0.9 else RelationType.RELATED,
                    confidence=confidence
                ))

        confidence_order = [
            MappingConfidence.EXACT,
            MappingConfidence.HIGH,
            MappingConfidence.MEDIUM,
            MappingConfidence.LOW,
            MappingConfidence.UNCERTAIN
        ]
        mappings.sort(key=lambda m: confidence_order.index(m.confidence))

        return MappingResult(
            source_field=field_name,
            source_value=field_value,
            mappings=mappings,
            best_match=mappings[0] if mappings else None,
            unmapped=len(mappings) == 0
        )

    def _normalize_value(self, value: str) -> str:
        prefixes = ["ifc", "cobie", "type", "element"]
        normalized = value.lower().strip()
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        return normalized.strip("_- ")

    def _matches(self, value: str, concept: str) -> bool:
        normalized_value = self._normalize_value(value)
        normalized_concept = self._normalize_value(concept)
        return normalized_value == normalized_concept

    def _calculate_similarity(self, value: str, concept: OntologyConcept) -> float:
        value_lower = value.lower()
        concept_name_lower = concept.name.lower()
        concept_id_lower = concept.id.lower()

        if value_lower == concept_name_lower or value_lower == concept_id_lower:
            return 1.0
        if value_lower in concept_name_lower or concept_name_lower in value_lower:
            return 0.8
        for key, synonyms in self.synonym_map.items():
            if key in value_lower:
                if key in concept_name_lower:
                    return 0.9
                for syn in synonyms:
                    if syn in concept_name_lower:
                        return 0.7
        if concept.definition:
            if value_lower in concept.definition.lower():
                return 0.6
        return 0.0

    def _similarity_to_confidence(self, similarity: float) -> MappingConfidence:
        if similarity >= 0.95:
            return MappingConfidence.EXACT
        elif similarity >= 0.8:
            return MappingConfidence.HIGH
        elif similarity >= 0.6:
            return MappingConfidence.MEDIUM
        elif similarity >= 0.4:
            return MappingConfidence.LOW
        else:
            return MappingConfidence.UNCERTAIN

    def map_schema(
        self,
        schema: Dict[str, List[str]],
        target_ontology: OntologyType = OntologyType.IFC
    ) -> OntologyMappingReport:
        all_mappings = []
        confidence_dist = {c.value: 0 for c in MappingConfidence}

        for field_name, sample_values in schema.items():
            value = sample_values[0] if sample_values else field_name
            result = self.map_field(field_name, value, target_ontology=target_ontology)
            all_mappings.append(result)
            if result.best_match:
                confidence_dist[result.best_match.confidence.value] += 1

        mapped = sum(1 for m in all_mappings if not m.unmapped)
        unmapped = len(all_mappings) - mapped
        coverage = mapped / len(all_mappings) if all_mappings else 0
        recommendations = self._generate_recommendations(all_mappings, coverage)

        return OntologyMappingReport(
            total_fields=len(all_mappings),
            mapped_fields=mapped,
            unmapped_fields=unmapped,
            mappings=all_mappings,
            coverage=coverage,
            confidence_distribution=confidence_dist,
            recommendations=recommendations
        )

    def _generate_recommendations(self, mappings: List[MappingResult], coverage: float) -> List[str]:
        recommendations = []
        if coverage < 0.7:
            recommendations.append(
                f"Low mapping coverage ({coverage:.0%}). Consider adding custom mappings."
            )
        low_confidence = [m for m in mappings
                         if m.best_match and m.best_match.confidence
                         in [MappingConfidence.LOW, MappingConfidence.UNCERTAIN]]
        if low_confidence:
            recommendations.append(
                f"{len(low_confidence)} mappings have low confidence. Review manually."
            )
        unmapped = [m for m in mappings if m.unmapped]
        if unmapped:
            fields = [m.source_field for m in unmapped[:5]]
            recommendations.append(
                f"Unmapped fields: {', '.join(fields)}. Add custom mappings."
            )
        return recommendations

    def create_mapping(
        self,
        source: str,
        source_ontology: OntologyType,
        target: str,
        target_ontology: OntologyType,
        relation: RelationType = RelationType.EQUIVALENT,
        notes: Optional[str] = None
    ) -> SemanticMapping:
        mapping = SemanticMapping(
            source_concept=source,
            source_ontology=source_ontology,
            target_concept=target,
            target_ontology=target_ontology,
            relation=relation,
            confidence=MappingConfidence.EXACT,
            notes=notes,
            created_by="manual"
        )
        self.mapping_rules.append(mapping)
        return mapping

    def export_mappings(self, format: str = "json") -> str:
        if format == "json":
            mappings_data = []
            for rule in self.mapping_rules:
                mappings_data.append({
                    "source": rule.source_concept,
                    "source_ontology": rule.source_ontology.value,
                    "target": rule.target_concept,
                    "target_ontology": rule.target_ontology.value,
                    "relation": rule.relation.value,
                    "confidence": rule.confidence.value
                })
            return json.dumps(mappings_data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def generate_report(self, report: OntologyMappingReport) -> str:
        output = f"""
# Ontology Mapping Report

## Summary
- **Total Fields:** {report.total_fields}
- **Mapped Fields:** {report.mapped_fields}
- **Unmapped Fields:** {report.unmapped_fields}
- **Coverage:** {report.coverage:.0%}

## Confidence Distribution
"""
        for conf, count in report.confidence_distribution.items():
            if count > 0:
                output += f"- **{conf.title()}:** {count}\n"

        output += "\n## Recommendations\n"
        for rec in report.recommendations:
            output += f"- {rec}\n"

        output += "\n## Mappings\n"
        for mapping in report.mappings[:20]:
            status = "✓" if not mapping.unmapped else "✗"
            target = mapping.best_match.target_concept if mapping.best_match else "unmapped"
            conf = mapping.best_match.confidence.value if mapping.best_match else "-"
            output += f"- {status} {mapping.source_field}: {mapping.source_value} → {target} ({conf})\n"

        return output
PYEOF

echo "Setup complete. ontology_mapper.py installed at /workspace/ontology_mapper.py"