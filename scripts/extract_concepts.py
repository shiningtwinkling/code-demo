#!/usr/bin/env python3
"""Extract article-level legal concepts from the EU AI Act PDF."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import RDFS, SKOS, XSD

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - optional dependency
    fitz = None

BASE_NS = "http://example.org/eu-ai-act#"
CONCEPT_NS = "http://example.org/eu-ai-act/concept#"
ARTICLE_LINE = re.compile(r"^Article\s+(\d+)\s*$")

# Lightweight lexical mapping from article titles to ontology category labels.
CATEGORY_RULES = [
    ("prohibited", "AI_System"),
    ("high-risk", "AI_System"),
    ("transparency", "Obligation"),
    ("obligation", "Obligation"),
    ("risk management", "Obligation"),
    ("governance", "Governance"),
    ("office", "Governance"),
    ("board", "Governance"),
    ("authority", "Governance"),
    ("sandbox", "Governance"),
    ("database", "Governance"),
]


def extract_articles_from_pdf(pdf_path: Path) -> dict[int, str]:
    """Parse article numbers and titles from the official PDF table-of-contents sections."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed. Install it or use --seed-only.")

    doc = fitz.open(pdf_path)
    articles: dict[int, str] = {}

    for page_index in range(doc.page_count):
        lines = [line.strip() for line in doc.load_page(page_index).get_text("text").splitlines()]
        for i, line in enumerate(lines):
            match = ARTICLE_LINE.match(line)
            if not match:
                continue
            article_no = int(match.group(1))

            # The next non-empty line is usually the title in the TOC pages.
            title = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j] and not lines[j].startswith("(") and not lines[j].startswith("OJ "):
                    title = lines[j]
                    break

            if title and article_no not in articles:
                articles[article_no] = title

    return articles


def infer_category(title: str) -> str:
    lowered = title.lower()
    for needle, category in CATEGORY_RULES:
        if needle in lowered:
            return category
    return "owl:Thing"


def build_concept_graph(articles: dict[int, str]) -> Graph:
    graph = Graph()
    euaia = Namespace(BASE_NS)
    concept = Namespace(CONCEPT_NS)

    graph.bind("euaia", euaia)
    graph.bind("concept", concept)
    graph.bind("skos", SKOS)
    graph.bind("rdfs", RDFS)

    graph.add((euaia.articleReference, RDF.type, RDF.Property))

    for article_no, title in sorted(articles.items()):
        node = concept[f"Article_{article_no}"]
        graph.add((node, RDF.type, SKOS.Concept))
        graph.add((node, SKOS.prefLabel, Literal(title, lang="en")))
        graph.add((node, RDFS.label, Literal(f"Article {article_no}: {title}", lang="en")))
        graph.add((node, euaia.articleReference, Literal(f"Article {article_no}", datatype=XSD.string)))
        graph.add((node, euaia.mappedToTopClass, Literal(infer_category(title), datatype=XSD.string)))

    return graph


def write_csv(articles: dict[int, str], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["article", "title", "mapped_top_class"])
        for article_no, title in sorted(articles.items()):
            writer.writerow([f"Article {article_no}", title, infer_category(title)])


def seed_articles() -> dict[int, str]:
    """Fallback concept list used when PDF parsing is unavailable."""
    return {
        5: "Prohibited AI practices",
        6: "Classification rules for high-risk AI systems",
        9: "Risk management system",
        10: "Data and data governance",
        13: "Transparency and provision of information to deployers",
        16: "Obligations of providers of high-risk AI systems",
        26: "Obligations of deployers of high-risk AI systems",
        27: "Fundamental rights impact assessment for high-risk AI systems",
        50: "Transparency obligations for providers and deployers of certain AI systems",
        53: "Obligations for providers of general-purpose AI models",
        55: "Obligations of providers of general-purpose AI models with systemic risk",
        57: "AI regulatory sandboxes",
        64: "AI Office",
        65: "Establishment and structure of the European Artificial Intelligence Board",
        70: "Designation of national competent authorities and single points of contact",
        71: "EU database for high-risk AI systems listed in Annex III",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract lightweight legal concepts from the EU AI Act PDF.")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("/Users/zhoujing/PycharmProjects/AIAO/EU AI ACT.pdf"),
        help="Path to the EU AI Act PDF file.",
    )
    parser.add_argument(
        "--out-ttl",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ontology" / "extracted_concepts.ttl",
        help="Output Turtle file for extracted concepts.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "documentation" / "extracted_concepts.csv",
        help="Output CSV file for extracted concepts.",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Use embedded seed concepts instead of parsing the PDF.",
    )
    args = parser.parse_args()

    if args.seed_only:
        articles = seed_articles()
    else:
        try:
            articles = extract_articles_from_pdf(args.pdf)
            if not articles:
                print("No article titles parsed from PDF; switching to seed concepts.")
                articles = seed_articles()
        except Exception as exc:  # pragma: no cover - fallback path
            print(f"PDF extraction failed ({exc}); switching to seed concepts.")
            articles = seed_articles()

    concept_graph = build_concept_graph(articles)
    args.out_ttl.parent.mkdir(parents=True, exist_ok=True)
    concept_graph.serialize(destination=args.out_ttl, format="turtle")
    write_csv(articles, args.out_csv)

    print(f"Extracted {len(articles)} concepts.")
    print(f"TTL written to: {args.out_ttl}")
    print(f"CSV written to: {args.out_csv}")


if __name__ == "__main__":
    main()
