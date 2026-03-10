#!/usr/bin/env python3
"""Run competency SPARQL queries and print sample results."""

from __future__ import annotations

from pathlib import Path

import pyparsing
from rdflib import Graph

# Compatibility patch for environments with older pyparsing + newer rdflib.
if not hasattr(pyparsing, "DelimitedList") and hasattr(pyparsing, "delimitedList"):
    pyparsing.DelimitedList = pyparsing.delimitedList

QUERIES = {
    "CQ1": """
PREFIX euaia: <http://example.org/eu-ai-act#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?system ?systemLabel ?obligation ?obligationLabel ?article
WHERE {
  ?system a euaia:High_Risk_AI_System ;
          rdfs:label ?systemLabel ;
          euaia:subject_to_obligation ?obligation .
  ?obligation a euaia:Obligation ;
              rdfs:label ?obligationLabel ;
              euaia:articleReference ?article .
}
ORDER BY ?system ?obligation
""",
    "CQ2": """
PREFIX euaia: <http://example.org/eu-ai-act#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?actor ?actorLabel ?actorType ?obligationLabel
WHERE {
  VALUES ?actorType {
    euaia:Provider
    euaia:Deployer
    euaia:Distributor
    euaia:Importer
    euaia:Authority
  }
  ?actor a ?actorType ;
         rdfs:label ?actorLabel ;
         euaia:subject_to_obligation ?obligation .
  ?obligation a euaia:Obligation ;
              rdfs:label ?obligationLabel .
}
ORDER BY ?actor ?obligationLabel
""",
    "CQ3": """
PREFIX euaia: <http://example.org/eu-ai-act#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?practice ?label ?obligationLabel
WHERE {
  ?practice a euaia:Prohibited_AI_Practice ;
            rdfs:label ?label ;
            euaia:subject_to_obligation ?obligation .
  ?obligation a euaia:Obligation ;
              rdfs:label ?obligationLabel .
}
ORDER BY ?practice
""",
    "CQ4": """
PREFIX euaia: <http://example.org/eu-ai-act#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?governance ?governanceLabel ?relation ?target
WHERE {
  VALUES ?governanceType {
    euaia:AI_Regulatory_Sandbox
    euaia:AI_Office
    euaia:European_AI_Board
    euaia:Advisory_Forum
    euaia:Scientific_Panel
    euaia:National_Competent_Authority
    euaia:EU_Database
  }
  {
    ?governance a ?governanceType ;
                rdfs:label ?governanceLabel ;
                euaia:regulates ?target .
    BIND("regulates" AS ?relation)
  }
  UNION
  {
    ?governance a ?governanceType ;
                rdfs:label ?governanceLabel ;
                euaia:governs ?target .
    BIND("governs" AS ?relation)
  }
}
ORDER BY ?governance ?relation ?target
""",
    "CQ5": """
PREFIX euaia: <http://example.org/eu-ai-act#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?model ?modelLabel ?provider ?providerLabel ?obligationLabel
WHERE {
  ?model a euaia:General_Purpose_AI_Model ;
         rdfs:label ?modelLabel ;
         euaia:subject_to_obligation ?obligation .
  ?obligation a euaia:GPAI_Systemic_Risk_Obligation ;
              rdfs:label ?obligationLabel .
  ?provider a euaia:Provider ;
            rdfs:label ?providerLabel ;
            euaia:provides ?model .
}
ORDER BY ?model
""",
}


def main() -> None:
    ontology_path = Path(__file__).resolve().parents[1] / "ontology" / "eu_ai_act_ontology.ttl"
    graph = Graph().parse(ontology_path, format="turtle")

    for name, query in QUERIES.items():
        rows = list(graph.query(query))
        print(f"{name}: {len(rows)} rows")
        for row in rows[:3]:
            print(f"  {row}")


if __name__ == "__main__":
    main()
