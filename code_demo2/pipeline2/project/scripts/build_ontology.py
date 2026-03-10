#!/usr/bin/env python3
"""Build a lightweight proof-of-concept ontology for the EU AI Act."""

from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef, XSD

BASE_NS = "http://example.org/eu-ai-act#"
EXAMPLE_NS = "http://example.org/eu-ai-act/instance#"


def resolve_class_ref(ns: Namespace, name: str) -> URIRef:
    """Resolve a class reference from local name or known external class."""
    if name == "owl:Thing":
        return OWL.Thing
    return ns[name]


def add_class(graph: Graph, ns: Namespace, name: str, parent: str, label: str, description: str, article: str) -> None:
    """Create a class with minimum legal annotations."""
    node = ns[name]
    graph.add((node, RDF.type, OWL.Class))
    if parent:
        graph.add((node, RDFS.subClassOf, resolve_class_ref(ns, parent)))
    graph.add((node, RDFS.label, Literal(label, lang="en")))
    graph.add((node, RDFS.comment, Literal(description, lang="en")))
    graph.add((node, ns.articleReference, Literal(article, datatype=XSD.string)))


def add_property(
    graph: Graph,
    ns: Namespace,
    name: str,
    domain: str,
    range_: str,
    label: str,
    description: str,
    article: str,
    inverse_of: str | None = None,
) -> None:
    """Create an object property with core annotations."""
    prop = ns[name]
    graph.add((prop, RDF.type, OWL.ObjectProperty))
    if domain:
        graph.add((prop, RDFS.domain, resolve_class_ref(ns, domain)))
    if range_:
        graph.add((prop, RDFS.range, resolve_class_ref(ns, range_)))
    graph.add((prop, RDFS.label, Literal(label, lang="en")))
    graph.add((prop, RDFS.comment, Literal(description, lang="en")))
    graph.add((prop, ns.articleReference, Literal(article, datatype=XSD.string)))
    if inverse_of:
        graph.add((prop, OWL.inverseOf, ns[inverse_of]))


def add_obligation_instance(
    graph: Graph,
    ns: Namespace,
    ex: Namespace,
    instance_name: str,
    obligation_class: str,
    label: str,
    description: str,
    article: str,
) -> URIRef:
    """Create an obligation individual linked to the obligation taxonomy."""
    instance = ex[instance_name]
    graph.add((instance, RDF.type, ns["Obligation"]))
    graph.add((instance, RDF.type, ns[obligation_class]))
    graph.add((instance, RDFS.label, Literal(label, lang="en")))
    graph.add((instance, RDFS.comment, Literal(description, lang="en")))
    graph.add((instance, ns.articleReference, Literal(article, datatype=XSD.string)))
    return instance


def link_subject_to_obligation(graph: Graph, ns: Namespace, subject: URIRef, obligation: URIRef) -> None:
    """Assert both obligation assignment directions explicitly."""
    graph.add((subject, ns.subject_to_obligation, obligation))
    graph.add((obligation, ns.obligation_for, subject))


def build_graph() -> Graph:
    graph = Graph()
    euaia = Namespace(BASE_NS)
    ex = Namespace(EXAMPLE_NS)

    graph.bind("euaia", euaia)
    graph.bind("ex", ex)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)

    graph.add((euaia.articleReference, RDF.type, OWL.AnnotationProperty))
    graph.add((euaia.articleReference, RDFS.label, Literal("EU AI Act article reference", lang="en")))

    # Top-level taxonomy
    add_class(graph, euaia, "AI_System", "owl:Thing", "AI System", "AI systems and AI models regulated under the Act.", "Article 3")
    add_class(graph, euaia, "Actor", "owl:Thing", "Actor", "Natural or legal persons and public bodies with duties under the Act.", "Article 3")
    add_class(graph, euaia, "Obligation", "owl:Thing", "Obligation", "Normative requirements imposed by the EU AI Act.", "Articles 5-56")
    add_class(graph, euaia, "Governance", "owl:Thing", "Governance", "Institutional and procedural governance components of the Act.", "Articles 57-71")

    # AI system classes
    add_class(graph, euaia, "Prohibited_AI_Practice", "AI_System", "Prohibited AI Practice", "AI practices prohibited due to unacceptable risk.", "Article 5")
    add_class(graph, euaia, "High_Risk_AI_System", "AI_System", "High-Risk AI System", "AI systems classified as high-risk requiring strict controls.", "Article 6")
    add_class(graph, euaia, "Certain_AI_System", "AI_System", "Certain AI System", "AI systems subject to transparency obligations.", "Article 50")
    add_class(graph, euaia, "General_Purpose_AI_Model", "AI_System", "General-Purpose AI Model", "General-purpose AI models with specific provider duties.", "Articles 51-55")

    # Actor classes
    add_class(graph, euaia, "Provider", "Actor", "Provider", "Entity that develops or places an AI system/model on the market.", "Articles 16, 53")
    add_class(graph, euaia, "Deployer", "Actor", "Deployer", "Entity using an AI system under its authority.", "Article 26")
    add_class(graph, euaia, "Distributor", "Actor", "Distributor", "Entity making an AI system available on the Union market.", "Article 24")
    add_class(graph, euaia, "Importer", "Actor", "Importer", "Entity placing AI systems from third countries on the Union market.", "Article 23")
    add_class(graph, euaia, "Authority", "Actor", "Authority", "Public authority with supervisory or enforcement functions.", "Article 70")

    # Obligation subclasses (proposed extension)
    add_class(graph, euaia, "Prohibition_Obligation", "Obligation", "Prohibition Obligation", "Obligation not to place on market or use prohibited AI practices.", "Article 5")
    add_class(graph, euaia, "Risk_Management_Obligation", "Obligation", "Risk Management Obligation", "Maintain a continuous risk management system for high-risk AI.", "Article 9")
    add_class(graph, euaia, "Data_Governance_Obligation", "Obligation", "Data Governance Obligation", "Ensure quality and governance of training, validation and test data.", "Article 10")
    add_class(graph, euaia, "Technical_Documentation_Obligation", "Obligation", "Technical Documentation Obligation", "Draw up technical documentation before placing high-risk AI on market.", "Article 11")
    add_class(graph, euaia, "Record_Keeping_Obligation", "Obligation", "Record-Keeping Obligation", "Enable logging and traceability of high-risk AI operations.", "Article 12")
    add_class(graph, euaia, "Transparency_Obligation", "Obligation", "Transparency Obligation", "Inform users or affected persons when required under transparency rules.", "Articles 13, 50")
    add_class(graph, euaia, "Human_Oversight_Obligation", "Obligation", "Human Oversight Obligation", "Ensure effective human oversight measures during operation.", "Article 14")
    add_class(graph, euaia, "Accuracy_Robustness_Cybersecurity_Obligation", "Obligation", "Accuracy/Robustness/Cybersecurity Obligation", "Ensure required levels of accuracy, robustness and cybersecurity.", "Article 15")
    add_class(graph, euaia, "Provider_Obligation", "Obligation", "Provider Obligation", "Comply with provider duties for high-risk AI systems.", "Article 16")
    add_class(graph, euaia, "Deployer_Obligation", "Obligation", "Deployer Obligation", "Comply with deployer duties for high-risk AI systems.", "Article 26")
    add_class(graph, euaia, "Authority_Cooperation_Obligation", "Obligation", "Authority Cooperation Obligation", "National authorities cooperate, coordinate and support enforcement tasks.", "Article 70")
    add_class(graph, euaia, "Fundamental_Rights_Impact_Assessment_Obligation", "Obligation", "Fundamental Rights Impact Assessment Obligation", "Conduct FRIA before specific high-risk deployments.", "Article 27")
    add_class(graph, euaia, "GPAI_Provider_Obligation", "Obligation", "GPAI Provider Obligation", "Comply with provider duties for general-purpose AI models.", "Article 53")
    add_class(graph, euaia, "GPAI_Systemic_Risk_Obligation", "Obligation", "GPAI Systemic Risk Obligation", "Additional obligations for GPAI models with systemic risk.", "Article 55")

    # Governance subclasses (proposed extension)
    add_class(graph, euaia, "AI_Regulatory_Sandbox", "Governance", "AI Regulatory Sandbox", "Controlled environment for testing innovative AI under supervision.", "Articles 57-58")
    add_class(graph, euaia, "AI_Office", "Governance", "AI Office", "EU-level office supporting implementation and oversight of GPAI.", "Article 64")
    add_class(graph, euaia, "European_AI_Board", "Governance", "European AI Board", "Body coordinating national authorities and Commission cooperation.", "Articles 65-66")
    add_class(graph, euaia, "Advisory_Forum", "Governance", "Advisory Forum", "Multi-stakeholder advisory forum to support implementation.", "Article 67")
    add_class(graph, euaia, "Scientific_Panel", "Governance", "Scientific Panel", "Independent scientific experts supporting governance tasks.", "Article 68")
    add_class(graph, euaia, "National_Competent_Authority", "Governance", "National Competent Authority", "Member State authority designated for implementation and supervision.", "Article 70")
    add_class(graph, euaia, "EU_Database", "Governance", "EU Database", "Registration infrastructure for high-risk AI systems.", "Article 71")

    # Core relationships
    add_property(
        graph,
        euaia,
        "subject_to_obligation",
        "owl:Thing",
        "Obligation",
        "subject to obligation",
        "Links an actor or system to an applicable legal obligation.",
        "Articles 5-56",
        inverse_of="obligation_for",
    )
    add_property(
        graph,
        euaia,
        "obligation_for",
        "Obligation",
        "owl:Thing",
        "obligation for",
        "Inverse link from an obligation to covered actors or systems.",
        "Articles 5-56",
    )
    add_property(
        graph,
        euaia,
        "provides",
        "Provider",
        "AI_System",
        "provides",
        "Provider places or makes available an AI system or model.",
        "Articles 16, 53",
    )
    add_property(
        graph,
        euaia,
        "deploys",
        "Deployer",
        "AI_System",
        "deploys",
        "Deployer uses an AI system in an operational context.",
        "Article 26",
    )
    add_property(
        graph,
        euaia,
        "distributes",
        "Distributor",
        "AI_System",
        "distributes",
        "Distributor makes an AI system available in the market chain.",
        "Article 24",
    )
    add_property(
        graph,
        euaia,
        "imports",
        "Importer",
        "AI_System",
        "imports",
        "Importer introduces an AI system from outside the Union market.",
        "Article 23",
    )
    add_property(
        graph,
        euaia,
        "regulates",
        "Governance",
        "AI_System",
        "regulates",
        "Governance body regulates or supervises a system category or instance.",
        "Articles 57-71",
        inverse_of="regulated_by",
    )
    add_property(
        graph,
        euaia,
        "regulated_by",
        "AI_System",
        "Governance",
        "regulated by",
        "System is regulated by a governance entity.",
        "Articles 57-71",
    )
    add_property(
        graph,
        euaia,
        "governs",
        "Governance",
        "Actor",
        "governs",
        "Governance body oversees or coordinates actor behaviour.",
        "Articles 64-71",
        inverse_of="governed_by",
    )
    add_property(
        graph,
        euaia,
        "governed_by",
        "Actor",
        "Governance",
        "governed by",
        "Actor is supervised by governance entities.",
        "Articles 64-71",
    )
    add_property(
        graph,
        euaia,
        "participates_in_sandbox",
        "Actor",
        "AI_Regulatory_Sandbox",
        "participates in sandbox",
        "Actor participates in an AI regulatory sandbox.",
        "Articles 57-58",
    )

    # Example obligation individuals
    obl_provider = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_provider_compliance",
        "Provider_Obligation",
        "Provider Compliance Duty",
        "Provider must satisfy duties for high-risk AI systems.",
        "Article 16",
    )
    obl_transparency = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_transparency_duty",
        "Transparency_Obligation",
        "Transparency Duty",
        "Transparency obligations for certain AI systems and information duties.",
        "Articles 13, 50",
    )
    obl_deployer = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_deployer_compliance",
        "Deployer_Obligation",
        "Deployer Compliance Duty",
        "Deployer must satisfy duties for operation of high-risk AI systems.",
        "Article 26",
    )
    obl_fria = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_fria",
        "Fundamental_Rights_Impact_Assessment_Obligation",
        "Fundamental Rights Impact Assessment Duty",
        "Deployer must perform FRIA where required before use.",
        "Article 27",
    )
    obl_risk_mgmt = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_risk_management",
        "Risk_Management_Obligation",
        "Risk Management Duty",
        "High-risk AI systems must use continuous risk management processes.",
        "Article 9",
    )
    obl_data_gov = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_data_governance",
        "Data_Governance_Obligation",
        "Data Governance Duty",
        "High-risk AI systems must meet data governance and data quality requirements.",
        "Article 10",
    )
    obl_prohibition = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_prohibition",
        "Prohibition_Obligation",
        "Prohibition Duty",
        "Prohibited AI practices must not be placed on the market or used.",
        "Article 5",
    )
    obl_gpai = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_gpai_provider",
        "GPAI_Provider_Obligation",
        "GPAI Provider Duty",
        "Provider must satisfy baseline obligations for general-purpose AI models.",
        "Article 53",
    )
    obl_gpai_sr = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_gpai_systemic_risk",
        "GPAI_Systemic_Risk_Obligation",
        "GPAI Systemic Risk Duty",
        "Additional duties apply to GPAI models classified with systemic risk.",
        "Article 55",
    )
    obl_authority = add_obligation_instance(
        graph,
        euaia,
        ex,
        "obl_authority_cooperation",
        "Authority_Cooperation_Obligation",
        "Authority Cooperation Duty",
        "National competent authorities cooperate and coordinate supervision.",
        "Article 70",
    )

    # Example individuals
    graph.add((ex.acmeProvider, RDF.type, euaia.Provider))
    graph.add((ex.acmeProvider, RDFS.label, Literal("ACME AI Provider", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.acmeProvider, obl_provider)
    link_subject_to_obligation(graph, euaia, ex.acmeProvider, obl_transparency)

    graph.add((ex.cityEmploymentOffice, RDF.type, euaia.Deployer))
    graph.add((ex.cityEmploymentOffice, RDFS.label, Literal("City Employment Office", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.cityEmploymentOffice, obl_deployer)
    link_subject_to_obligation(graph, euaia, ex.cityEmploymentOffice, obl_fria)

    graph.add((ex.creditScoringAISystem, RDF.type, euaia.High_Risk_AI_System))
    graph.add((ex.creditScoringAISystem, RDFS.label, Literal("Credit Scoring AI System", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.creditScoringAISystem, obl_risk_mgmt)
    link_subject_to_obligation(graph, euaia, ex.creditScoringAISystem, obl_data_gov)

    graph.add((ex.socialScoringEngine, RDF.type, euaia.Prohibited_AI_Practice))
    graph.add((ex.socialScoringEngine, RDFS.label, Literal("Social Scoring Engine", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.socialScoringEngine, obl_prohibition)

    graph.add((ex.foundationModelX, RDF.type, euaia.General_Purpose_AI_Model))
    graph.add((ex.foundationModelX, RDFS.label, Literal("Foundation Model X", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.foundationModelX, obl_gpai)
    link_subject_to_obligation(graph, euaia, ex.foundationModelX, obl_gpai_sr)

    graph.add((ex.chatbotService, RDF.type, euaia.Certain_AI_System))
    graph.add((ex.chatbotService, RDFS.label, Literal("Public Service Chatbot", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.chatbotService, obl_transparency)

    graph.add((ex.euAIOffice, RDF.type, euaia.AI_Office))
    graph.add((ex.euAIOffice, RDFS.label, Literal("EU AI Office", lang="en")))

    graph.add((ex.europeanAIBoard, RDF.type, euaia.European_AI_Board))
    graph.add((ex.europeanAIBoard, RDFS.label, Literal("European AI Board", lang="en")))

    graph.add((ex.euDatabaseNode, RDF.type, euaia.EU_Database))
    graph.add((ex.euDatabaseNode, RDFS.label, Literal("EU High-Risk AI Database", lang="en")))

    graph.add((ex.franceAuthority, RDF.type, euaia.Authority))
    graph.add((ex.franceAuthority, RDF.type, euaia.National_Competent_Authority))
    graph.add((ex.franceAuthority, RDFS.label, Literal("French AI Competent Authority", lang="en")))
    link_subject_to_obligation(graph, euaia, ex.franceAuthority, obl_authority)

    graph.add((ex.regulatorySandboxFR, RDF.type, euaia.AI_Regulatory_Sandbox))
    graph.add((ex.regulatorySandboxFR, RDFS.label, Literal("French AI Sandbox", lang="en")))

    # Example relationships
    graph.add((ex.acmeProvider, euaia.provides, ex.creditScoringAISystem))
    graph.add((ex.acmeProvider, euaia.provides, ex.foundationModelX))
    graph.add((ex.cityEmploymentOffice, euaia.deploys, ex.creditScoringAISystem))
    graph.add((ex.creditScoringAISystem, euaia.regulated_by, ex.euDatabaseNode))
    graph.add((ex.foundationModelX, euaia.regulated_by, ex.euAIOffice))
    graph.add((ex.chatbotService, euaia.regulated_by, ex.franceAuthority))
    graph.add((ex.euAIOffice, euaia.regulates, ex.foundationModelX))
    graph.add((ex.euDatabaseNode, euaia.regulates, ex.creditScoringAISystem))
    graph.add((ex.franceAuthority, euaia.governs, ex.cityEmploymentOffice))
    graph.add((ex.europeanAIBoard, euaia.governs, ex.franceAuthority))
    graph.add((ex.regulatorySandboxFR, euaia.governs, ex.acmeProvider))
    graph.add((ex.cityEmploymentOffice, euaia.governed_by, ex.franceAuthority))
    graph.add((ex.acmeProvider, euaia.participates_in_sandbox, ex.regulatorySandboxFR))

    return graph


def main() -> None:
    output_path = Path(__file__).resolve().parents[1] / "ontology" / "eu_ai_act_ontology.ttl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    graph.serialize(destination=output_path, format="turtle")
    print(f"Ontology written to {output_path}")


if __name__ == "__main__":
    main()
