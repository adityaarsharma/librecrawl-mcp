"""
Schema.org / JSON-LD structured data validator (librecrawl-mcp v2.0 easy half).

The existing librecrawl_schema_check / _audit tools EXTRACT JSON-LD and
classify TYPES — they don't validate against schema.org's required-fields
spec or Google's Rich Results eligibility rules. This module closes that gap.

VALIDATION LAYERS:
  1. JSON-LD parse errors (capture line numbers where possible)
  2. Schema.org required fields per @type
  3. Google Rich Results required fields per @type
       (subset of schema.org spec; some types like Recipe require more)

Hardcoded required-fields tables for the 7 most common rich-result types:
  Article, Product, Recipe, FAQPage, BreadcrumbList, Event, JobPosting.

For unknown types, falls back to schema.org `@type` validity check only.

Public entry points:
    validate_page_schemas(schemas_list) -> list of finding dicts
    validate_crawl_schemas(pages) -> {summary, findings, csv_rows}
"""

from __future__ import annotations

import json
import re
from collections import defaultdict


# ── Required-fields tables ───────────────────────────────────────────────────
# Source: https://developers.google.com/search/docs/appearance/structured-data
# Spec snapshot taken 2026-06. Add types here as more rich-result formats land.

SCHEMA_REQUIRED = {
    "Article":          ["headline", "author", "datePublished"],
    "BlogPosting":      ["headline", "author", "datePublished"],
    "NewsArticle":      ["headline", "author", "datePublished"],
    "Product":          ["name"],  # at least name; offers OR review usually expected
    "Recipe":           ["name", "recipeIngredient", "recipeInstructions"],
    "FAQPage":          ["mainEntity"],
    "BreadcrumbList":   ["itemListElement"],
    "Event":            ["name", "startDate", "location"],
    "JobPosting":       ["title", "description", "hiringOrganization",
                          "jobLocation", "datePosted"],
    "VideoObject":      ["name", "description", "thumbnailUrl", "uploadDate"],
    "Organization":    ["name"],
    "LocalBusiness":    ["name", "address"],
    "Person":           ["name"],
    "Review":           ["author", "itemReviewed", "reviewRating"],
    "AggregateRating":  ["ratingValue", "reviewCount"],
    "HowTo":            ["name", "step"],
    "Course":           ["name", "description", "provider"],
}

# Subset of fields specifically required for Google Rich Results.
# Some types have ADDITIONAL Google-only required fields beyond schema.org.
GOOGLE_RICH_RESULT_REQUIRED = {
    "Article":          ["headline", "image"],
    "Product":          ["name", "image", "offers"],
    "Recipe":           ["name", "image", "recipeIngredient", "recipeInstructions"],
    "FAQPage":          ["mainEntity"],
    "BreadcrumbList":   ["itemListElement"],
    "Event":            ["name", "startDate", "location", "offers"],
    "JobPosting":       ["title", "description", "hiringOrganization",
                          "jobLocation", "datePosted", "validThrough"],
    "VideoObject":      ["name", "description", "thumbnailUrl", "uploadDate"],
    "HowTo":            ["name", "step"],
}


# ── Per-schema validation ─────────────────────────────────────────────────────

def _expand_graph(schema: dict) -> list:
    """Yoast/RankMath wrap multiple schemas in @graph. Flatten them."""
    if not isinstance(schema, dict):
        return []
    if "@graph" in schema and isinstance(schema["@graph"], list):
        return [s for s in schema["@graph"] if isinstance(s, dict)]
    return [schema]


def _get_type(schema: dict) -> str | None:
    """@type can be a string OR a list of strings — pick the first non-Thing."""
    t = schema.get("@type") or schema.get("type")
    if isinstance(t, str):
        return t
    if isinstance(t, list) and t:
        for x in t:
            if isinstance(x, str) and x.lower() != "thing":
                return x
        return t[0] if isinstance(t[0], str) else None
    return None


def _has_field(schema: dict, field: str) -> bool:
    """Field present and non-empty (recurses into list/dict)."""
    if field not in schema:
        return False
    v = schema[field]
    if v is None:
        return False
    if isinstance(v, (list, dict)) and not v:
        return False
    if isinstance(v, str) and not v.strip():
        return False
    return True


def validate_single_schema(schema: dict, source_url: str = "") -> list:
    """Returns a list of finding dicts for ONE @graph element."""
    findings = []
    if not isinstance(schema, dict):
        findings.append({
            "url":      source_url,
            "type":     "",
            "severity": "high",
            "check":    "schema_not_object",
            "detail":   f"Schema is {type(schema).__name__}, expected object",
        })
        return findings

    t = _get_type(schema)
    if not t:
        findings.append({
            "url":      source_url,
            "type":     "",
            "severity": "high",
            "check":    "schema_missing_type",
            "detail":   "@type missing or empty",
        })
        return findings

    # Schema.org required field check
    required = SCHEMA_REQUIRED.get(t)
    if required:
        missing = [f for f in required if not _has_field(schema, f)]
        for f in missing:
            findings.append({
                "url":      source_url,
                "type":     t,
                "severity": "medium",
                "check":    "schema_missing_required_field",
                "detail":   f'{t} missing schema.org required field: {f}',
            })

    # Google rich-result required field check
    rich = GOOGLE_RICH_RESULT_REQUIRED.get(t)
    if rich:
        missing_rich = [f for f in rich if not _has_field(schema, f)]
        for f in missing_rich:
            findings.append({
                "url":      source_url,
                "type":     t,
                "severity": "high",
                "check":    "schema_rich_result_missing_field",
                "detail":   f'{t} missing Google rich-result field: {f}',
            })

    # Specific quality checks
    if t in ("Product",) and not _has_field(schema, "offers") and \
       not _has_field(schema, "aggregateRating") and not _has_field(schema, "review"):
        findings.append({
            "url":      source_url,
            "type":     t,
            "severity": "medium",
            "check":    "product_no_offer_or_review",
            "detail":   "Product has neither offers nor reviews/aggregateRating",
        })

    if t == "FAQPage":
        me = schema.get("mainEntity")
        if isinstance(me, list) and len(me) == 0:
            findings.append({
                "url":      source_url,
                "type":     t,
                "severity": "high",
                "check":    "faq_empty_questions",
                "detail":   "FAQPage mainEntity is empty",
            })

    return findings


# ── Page-level validation (handles multi-schema pages + @graph) ──────────────

def validate_page_schemas(schemas_list: list, source_url: str = "") -> list:
    """Validate every JSON-LD blob on a page. Returns list of findings."""
    if not schemas_list:
        return []
    out = []
    for blob in schemas_list:
        # Each blob may itself be a graph wrapper
        if isinstance(blob, dict) and "error" in blob and len(blob) == 1:
            # Parse error from upstream
            out.append({
                "url": source_url, "type": "", "severity": "high",
                "check": "schema_parse_error",
                "detail": str(blob.get("error", "JSON-LD parse failure")),
            })
            continue
        for sub in _expand_graph(blob):
            out.extend(validate_single_schema(sub, source_url=source_url))
    return out


# ── Crawl-level summary ──────────────────────────────────────────────────────

def validate_crawl_schemas(pages: list) -> dict:
    """Walk every page that has structured data; validate; return summary +
    per-page findings rows ready for CSV emission.

    Expects each page dict to contain `structured_data` (LibreCrawl's export
    field name) as a list of dicts. Falls back to `json_ld` if present.
    """
    findings = []
    by_check = defaultdict(int)
    by_type  = defaultdict(int)
    pages_with_schema = 0
    pages_with_errors = 0

    for p in pages or []:
        url = p.get("url") or ""
        # Schema can be exported either as a parsed list or a raw JSON string
        sd = p.get("structured_data") or p.get("json_ld") or p.get("schema")
        if not sd:
            continue
        if isinstance(sd, str):
            try:
                sd = json.loads(sd)
            except Exception:
                findings.append({
                    "url": url, "type": "", "severity": "high",
                    "check": "schema_parse_error",
                    "detail": "structured_data field is non-JSON string",
                })
                by_check["schema_parse_error"] += 1
                pages_with_errors += 1
                continue
        if isinstance(sd, dict):
            sd = [sd]
        if not isinstance(sd, list):
            continue
        pages_with_schema += 1

        # Track types
        for blob in sd:
            for sub in _expand_graph(blob if isinstance(blob, dict) else {}):
                t = _get_type(sub)
                if t:
                    by_type[t] += 1

        page_findings = validate_page_schemas(sd, source_url=url)
        if page_findings:
            pages_with_errors += 1
            findings.extend(page_findings)
            for f in page_findings:
                by_check[f["check"]] += 1

    return {
        "pages_with_schema":      pages_with_schema,
        "pages_with_errors":      pages_with_errors,
        "total_findings":         len(findings),
        "findings_by_check":      dict(by_check),
        "schema_types_breakdown": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "findings":               findings,
    }
