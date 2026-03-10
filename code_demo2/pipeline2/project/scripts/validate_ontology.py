#!/usr/bin/env python3
"""Validate ontology quality with SHACL (if available) and fallback rule checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.term import URIRef

BASE_NS = "http://example.org/eu-ai-act#"

CORE_CLASSES = [
    "AI_System",
    "Prohibited_AI_Practice",
    "High_Risk_AI_System",
    "Certain_AI_System",
    "General_Purpose_AI_Model",
    "Actor",
    "Provider",
    "Deployer",
    "Distributor",
    "Importer",
    "Authority",
    "Obligation",
    "Governance",
    "AI_Office",
    "European_AI_Board",
    "National_Competent_Authority",
    "EU_Database",
]


def run_pyshacl(data_graph: Graph, shapes_graph: Graph) -> tuple[bool, str] | None:
    """Run SHACL with pyshacl if it is installed."""
    try:
        from pyshacl import validate  # type: ignore
    except ImportError:
        return None

    conforms, _, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        allow_infos=True,
        allow_warnings=True,
    )
    return bool(conforms), str(results_text)


def get_subclasses(graph: Graph, class_uri: URIRef) -> set[URIRef]:
    """Return class_uri and all transitive subclasses."""
    pending = [class_uri]
    seen: set[URIRef] = set()

    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for subclass in graph.subjects(RDFS.subClassOf, current):
            if isinstance(subclass, URIRef) and subclass not in seen:
                pending.append(subclass)

    return seen


def get_instances_of(graph: Graph, class_uri: URIRef) -> set[URIRef]:
    """Return instances typed with class_uri or any transitive subclass."""
    class_set = get_subclasses(graph, class_uri)
    instances: set[URIRef] = set()

    for candidate in class_set:
        for instance in graph.subjects(RDF.type, candidate):
            if isinstance(instance, URIRef):
                instances.add(instance)

    return instances


def run_manual_checks(graph: Graph) -> list[str]:
    """Fallback checks for reproducible validation without SPARQL/extra deps."""
    euaia = Namespace(BASE_NS)
    failures: list[str] = []

    # Metadata coverage for a compact set of core classes.
    for cls_name in CORE_CLASSES:
        cls = euaia[cls_name]
        if not list(graph.objects(cls, RDFS.label)):
            failures.append(f"Missing rdfs:label for class {cls_name}")
        if not list(graph.objects(cls, RDFS.comment)):
            failures.append(f"Missing rdfs:comment for class {cls_name}")
        if not list(graph.objects(cls, euaia.articleReference)):
            failures.append(f"Missing articleReference for class {cls_name}")

    # Actors should have at least one obligation.
    for actor in sorted(get_instances_of(graph, euaia.Actor), key=str):
        if not list(graph.objects(actor, euaia.subject_to_obligation)):
            failures.append(f"Actor without obligation: {actor}")

    # High-risk AI systems should have duties and governance links.
    for system in sorted(get_instances_of(graph, euaia.High_Risk_AI_System), key=str):
        if not list(graph.objects(system, euaia.subject_to_obligation)):
            failures.append(f"High-risk AI system without obligation: {system}")
        if not list(graph.objects(system, euaia.regulated_by)):
            failures.append(f"High-risk AI system without governance link: {system}")

    # Governance nodes should regulate systems, govern actors, or host sandbox participants.
    for gov in sorted(get_instances_of(graph, euaia.Governance), key=str):
        has_regulation = bool(list(graph.objects(gov, euaia.regulates)))
        has_governance = bool(list(graph.objects(gov, euaia.governs)))
        has_sandbox_participant = bool(list(graph.subjects(euaia.participates_in_sandbox, gov)))
        if not (has_regulation or has_governance or has_sandbox_participant):
            failures.append(f"Governance node without operational link: {gov}")

    # Obligation instances should point to at least one covered entity.
    for obligation in sorted(get_instances_of(graph, euaia.Obligation), key=str):
        if not list(graph.objects(obligation, euaia.obligation_for)):
            failures.append(f"Obligation instance without obligation_for relation: {obligation}")

    # Every actor/system/governance/obligation instance should have at least one operational relation.
    relation_predicates = [
        euaia.subject_to_obligation,
        euaia.obligation_for,
        euaia.provides,
        euaia.deploys,
        euaia.distributes,
        euaia.imports,
        euaia.regulates,
        euaia.regulated_by,
        euaia.governs,
        euaia.governed_by,
        euaia.participates_in_sandbox,
    ]
    tracked_instances = set()
    tracked_instances.update(get_instances_of(graph, euaia.Actor))
    tracked_instances.update(get_instances_of(graph, euaia.AI_System))
    tracked_instances.update(get_instances_of(graph, euaia.Governance))
    tracked_instances.update(get_instances_of(graph, euaia.Obligation))

    for instance in sorted(tracked_instances, key=str):
        has_relation = any(bool(list(graph.objects(instance, predicate))) for predicate in relation_predicates)
        if not has_relation:
            failures.append(f"Instance without operational relation: {instance}")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate EU AI Act ontology and SHACL shapes.")
    parser.add_argument(
        "--ontology",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ontology" / "eu_ai_act_ontology.ttl",
        help="Path to ontology Turtle file.",
    )
    parser.add_argument(
        "--shapes",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "shapes" / "validation_shapes.ttl",
        help="Path to SHACL shapes Turtle file.",
    )
    args = parser.parse_args()

    data_graph = Graph().parse(args.ontology, format="turtle")
    shapes_graph = Graph().parse(args.shapes, format="turtle")

    pyshacl_result = run_pyshacl(data_graph, shapes_graph)
    if pyshacl_result is not None:
        conforms, report = pyshacl_result
        print("SHACL result:", "PASS" if conforms else "FAIL")
        if not conforms:
            print(report)
    else:
        print("pyshacl not installed; running manual validation checks.")

    failures = run_manual_checks(data_graph)

    if failures:
        print("Manual validation result: FAIL")
        for issue in failures:
            print(f"- {issue}")
        raise SystemExit(1)

    print("Manual validation result: PASS")


if __name__ == "__main__":
    main()
