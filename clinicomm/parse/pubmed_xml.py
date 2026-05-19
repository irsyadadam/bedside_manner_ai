"""Parse a PubMed EFetch XML response into ParsedDocument objects.

The PubMed DTD is messier than it looks. Notable handled cases:
  - AbstractText with Label= and/or NlmCategory= (structured abstracts).
  - Inline mark-up inside titles/abstracts (<b>, <i>, <sub>, <sup>) —
    flattened with itertext().
  - Authors as either (LastName + ForeName) or CollectiveName.
  - MeshHeading: MajorTopicYN on DescriptorName OR any QualifierName
    marks the heading as major_topic.
  - PubDate: Year + Month (name or number) + Day, with MedlineDate
    fallback (e.g., "2024 Spring").
"""
from __future__ import annotations

from typing import Iterator

from lxml import etree

from clinicomm.schemas import AbstractSection, Author, MeshHeading, ParsedDocument

_MONTH = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_pubmed_articles(xml_bytes: bytes) -> Iterator[tuple[str, etree._Element, ParsedDocument | None, str | None]]:
    """Yield (pmid, article_element, parsed_or_None, drop_reason) for each
    <PubmedArticle> in the EFetch XML response.

    The caller decides what to do with parsed=None records (typically:
    save raw XML, skip JSON, count as dropped). drop_reason is a short
    string explaining why parsed is None.
    """
    root = etree.fromstring(xml_bytes)
    for article in root.iter("PubmedArticle"):
        pmid_node = article.find(".//MedlineCitation/PMID")
        if pmid_node is None or not (pmid_node.text or "").strip():
            yield ("", article, None, "no_pmid")
            continue
        pmid = pmid_node.text.strip()
        try:
            parsed = parse_one(article, pmid=pmid)
        except Exception as e:  # noqa: BLE001
            yield (pmid, article, None, f"parse_error: {type(e).__name__}: {e}")
            continue
        if not parsed.abstract:
            yield (pmid, article, None, "no_abstract")
            continue
        yield (pmid, article, parsed, None)


def parse_one(article: etree._Element, pmid: str | None = None) -> ParsedDocument:
    if pmid is None:
        pmid = (article.findtext(".//MedlineCitation/PMID") or "").strip()
        if not pmid:
            raise ValueError("missing PMID")

    title = _text_join(article.find(".//Article/ArticleTitle"))
    abstract = _parse_abstract(article)
    journal = (
        article.findtext(".//Article/Journal/Title")
        or article.findtext(".//Article/Journal/ISOAbbreviation")
        or None
    )
    pub_date = _parse_pubdate(article.find(".//Article/Journal/JournalIssue/PubDate"))
    pub_types = [
        (pt.text or "").strip()
        for pt in article.findall(".//Article/PublicationTypeList/PublicationType")
        if (pt.text or "").strip()
    ]
    mesh_headings = _parse_mesh(article)
    authors, issuing_body = _parse_authors(article)
    doi = _parse_doi(article)

    return ParsedDocument(
        pmid=pmid,
        doi=doi,
        title=title,
        abstract=abstract,
        journal=journal,
        pub_date=pub_date,
        pub_types=pub_types,
        mesh_headings=mesh_headings,
        authors=authors,
        issuing_body=issuing_body,
    )


# -- helpers ----------------------------------------------------------------


def _text_join(node: etree._Element | None) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split()).strip()


def _parse_abstract(article: etree._Element) -> list[AbstractSection]:
    sections: list[AbstractSection] = []
    for at in article.findall(".//Article/Abstract/AbstractText"):
        text = _text_join(at)
        if not text:
            continue
        label = at.get("Label") or at.get("NlmCategory") or None
        if label:
            label = label.strip() or None
        sections.append(AbstractSection(section_label=label, text=text))
    # Some records also use OtherAbstract — skip; not the article's own abstract.
    return sections


def _parse_pubdate(node: etree._Element | None) -> str | None:
    if node is None:
        return None
    medline = (node.findtext("MedlineDate") or "").strip()
    if medline and not node.findtext("Year"):
        return medline
    year = (node.findtext("Year") or "").strip()
    if not year:
        return medline or None
    month_raw = (node.findtext("Month") or "").strip()
    day_raw = (node.findtext("Day") or "").strip()
    month_num: int | None = None
    if month_raw.isdigit():
        month_num = int(month_raw)
    elif month_raw:
        month_num = _MONTH.get(month_raw[:3].lower())
    if month_num is None:
        return year
    if not day_raw.isdigit():
        return f"{year}-{month_num:02d}"
    return f"{year}-{month_num:02d}-{int(day_raw):02d}"


def _parse_mesh(article: etree._Element) -> list[MeshHeading]:
    out: list[MeshHeading] = []
    for mh in article.findall(".//MeshHeadingList/MeshHeading"):
        desc = mh.find("DescriptorName")
        if desc is None or not (desc.text or "").strip():
            continue
        major = desc.get("MajorTopicYN") == "Y"
        quals: list[str] = []
        for q in mh.findall("QualifierName"):
            qt = (q.text or "").strip()
            if qt:
                quals.append(qt)
            if q.get("MajorTopicYN") == "Y":
                major = True
        out.append(
            MeshHeading(descriptor=desc.text.strip(), qualifiers=quals, major_topic=major)
        )
    return out


def _parse_authors(article: etree._Element) -> tuple[list[Author], str | None]:
    authors: list[Author] = []
    issuing_body: str | None = None
    for au in article.findall(".//Article/AuthorList/Author"):
        collective = (au.findtext("CollectiveName") or "").strip()
        if collective:
            if issuing_body is None:
                issuing_body = collective
            authors.append(Author(name=collective, is_collective=True))
            continue
        last = (au.findtext("LastName") or "").strip()
        fore = (au.findtext("ForeName") or au.findtext("Initials") or "").strip()
        name = (f"{fore} {last}").strip()
        if not name:
            continue
        aff = (
            au.findtext("AffiliationInfo/Affiliation")
            or au.findtext("Affiliation")
            or ""
        ).strip() or None
        authors.append(Author(name=name, affiliation=aff))
    return authors, issuing_body


def _parse_doi(article: etree._Element) -> str | None:
    for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        if aid.get("IdType") == "doi" and (aid.text or "").strip():
            return aid.text.strip()
    # Fallback: ELocationID with EIdType=doi
    for el in article.findall(".//Article/ELocationID"):
        if el.get("EIdType") == "doi" and (el.text or "").strip():
            return el.text.strip()
    return None
