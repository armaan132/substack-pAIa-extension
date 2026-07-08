"""Citation sentiment analysis for newsletter recommendation signals.

This module analyzes locally saved post HTML, extracts links to other Substack
posts/newsletters, scores the author's surrounding context, and writes those
signals back into ``data/index.json``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised when optional deps are absent
    BeautifulSoup = None

try:
    from textblob import TextBlob
except ImportError:  # pragma: no cover - exercised when optional deps are absent
    TextBlob = None


SUBSTACK_HOST_RE = re.compile(r"(^|\.)substack\.com$", re.IGNORECASE)
SUBSTACK_POST_PATH_RE = re.compile(r"^/p/[^/]+/?$", re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
ANCHOR_RE = re.compile(
    r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<text>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
CONTRAST_RE = re.compile(r"\b(but|however|still|although|though|yet)\b", re.IGNORECASE)
NEGATION_RE = re.compile(r"\b(no|not|never|hardly|rarely|without|isn't|aren't|wasn't|weren't|don't|doesn't|didn't)\b", re.IGNORECASE)
HEDGE_RE = re.compile(r"\b(maybe|perhaps|somewhat|partly|sort of|kind of|seems|appears|might|could)\b", re.IGNORECASE)
EVALUATION_TARGET_RE = re.compile(
    r"\b(argument|essay|post|piece|claim|analysis|forecast|evidence|conclusion|model|thread|write[- ]?up)\b",
    re.IGNORECASE,
)
SUPPORTIVE_PATTERNS: List[Tuple[re.Pattern, float, str]] = [
    (re.compile(r"\b(strongly )?recommend(?:ed|s|ing)?\b", re.IGNORECASE), 1.2, "recommend"),
    (re.compile(r"\bworth (reading|your time|checking out|a read)\b", re.IGNORECASE), 1.1, "worth reading"),
    (re.compile(r"\b(excellent|great|smart|insightful|helpful|useful|persuasive|careful|convincing|strong|valuable|important)\b", re.IGNORECASE), 0.8, "positive evaluation"),
    (re.compile(r"\b(i agree|agree with|right about|gets? this right)\b", re.IGNORECASE), 0.9, "agreement"),
    (re.compile(r"\b(good evidence|strong evidence|well argued|well-argued|well researched|well-researched)\b", re.IGNORECASE), 1.0, "strong evidence"),
]
CRITICAL_PATTERNS: List[Tuple[re.Pattern, float, str]] = [
    (re.compile(r"\b(weak|misleading|wrong|flawed|poor|shallow|careless|unconvincing|dubious|confused|false|overstated|overstates)\b", re.IGNORECASE), -0.8, "negative evaluation"),
    (re.compile(r"\b(bad look|bad argument|bad evidence|bad analysis)\b", re.IGNORECASE), -0.7, "bad evaluation"),
    (re.compile(r"\b(i disagree|disagree with|not convinced|unpersuaded|would not rely on)\b", re.IGNORECASE), -1.0, "disagreement"),
    (re.compile(r"\b(strawman|straw man|fails? to|does not address|misses? the point)\b", re.IGNORECASE), -0.9, "critique"),
    (re.compile(r"\b(lacks evidence|unsupported|no evidence)\b", re.IGNORECASE), -1.0, "weak evidence"),
]
NEUTRAL_CITATION_RE = re.compile(
    r"\b(see also|via|published|discusses|mentions|links? to|according to|as noted by|in the past|last week)\b",
    re.IGNORECASE,
)


@dataclass
class CitationAnalysisResult:
    """Structured result for a single linked post/newsletter citation."""

    target_url: str
    target_newsletter_url: str
    target_domain: str
    anchor_text: str
    context: str
    sentiment: str
    polarity: float
    subjectivity: float
    confidence: float
    recommendation_signal: float
    reliability: str
    evidence: List[str]
    is_known_newsletter: bool

    def as_dict(self) -> Dict:
        return {
            "target_url": self.target_url,
            "target_newsletter_url": self.target_newsletter_url,
            "target_domain": self.target_domain,
            "anchor_text": self.anchor_text,
            "context": self.context,
            "sentiment": self.sentiment,
            "polarity": self.polarity,
            "subjectivity": self.subjectivity,
            "confidence": self.confidence,
            "recommendation_signal": self.recommendation_signal,
            "reliability": self.reliability,
            "evidence": self.evidence,
            "is_known_newsletter": self.is_known_newsletter,
        }


class CitationSentimentAnalyzer:
    """Analyze author feedback toward cited Substack posts/newsletters."""

    def __init__(self, known_newsletter_urls: Optional[Iterable[str]] = None):
        self.known_newsletter_urls = {
            normalize_newsletter_url(url) for url in (known_newsletter_urls or [])
        }

    def analyze_html(
        self,
        html: str,
        source_url: str = "",
        context_window: int = 2,
    ) -> List[Dict]:
        """Return citation sentiment records extracted from one HTML document."""
        if BeautifulSoup is None:
            return self._analyze_html_without_bs4(html, source_url)

        soup = BeautifulSoup(html, "html.parser")
        content = (
            soup.find("div", attrs={"data-testid": "post-content"})
            or soup.find("article")
            or soup.body
            or soup
        )

        source_normalized = normalize_url(source_url) if source_url else ""
        results: List[CitationAnalysisResult] = []
        seen_targets = set()

        for link in content.find_all("a", href=True):
            target_url = normalize_url(link["href"])
            if not is_substack_post_url(target_url):
                continue
            if source_normalized and target_url == source_normalized:
                continue
            if target_url in seen_targets:
                continue

            anchor_text = link.get_text(" ", strip=True)
            context = extract_link_context(link, anchor_text, context_window)
            if not context:
                continue

            target_newsletter_url = normalize_newsletter_url(target_url)
            sentiment = score_author_stance(context, anchor_text)
            seen_targets.add(target_url)
            results.append(
                CitationAnalysisResult(
                    target_url=target_url,
                    target_newsletter_url=target_newsletter_url,
                    target_domain=urlparse(target_newsletter_url).netloc,
                    anchor_text=anchor_text[:160],
                    context=unescape(context[:500]),
                    sentiment=sentiment["label"],
                    polarity=sentiment["polarity"],
                    subjectivity=sentiment["subjectivity"],
                    confidence=sentiment["confidence"],
                    recommendation_signal=sentiment["recommendation_signal"],
                    reliability=sentiment["reliability"],
                    evidence=sentiment["evidence"],
                    is_known_newsletter=target_newsletter_url in self.known_newsletter_urls,
                )
            )

        return [result.as_dict() for result in results]

    def _analyze_html_without_bs4(self, html: str, source_url: str = "") -> List[Dict]:
        """Fallback citation extraction when BeautifulSoup is not installed."""
        source_normalized = normalize_url(source_url) if source_url else ""
        full_text = collapse_whitespace(strip_tags(html))
        results: List[CitationAnalysisResult] = []
        seen_targets = set()

        for match in ANCHOR_RE.finditer(html):
            target_url = normalize_url(match.group("href"))
            if not is_substack_post_url(target_url):
                continue
            if source_normalized and target_url == source_normalized:
                continue
            if target_url in seen_targets:
                continue

            anchor_text = collapse_whitespace(strip_tags(match.group("text")))
            context = extract_plain_text_context(full_text, anchor_text)
            if not context:
                continue

            target_newsletter_url = normalize_newsletter_url(target_url)
            sentiment = score_author_stance(context, anchor_text)
            seen_targets.add(target_url)
            results.append(
                CitationAnalysisResult(
                    target_url=target_url,
                    target_newsletter_url=target_newsletter_url,
                    target_domain=urlparse(target_newsletter_url).netloc,
                    anchor_text=anchor_text[:160],
                    context=unescape(context[:500]),
                    sentiment=sentiment["label"],
                    polarity=sentiment["polarity"],
                    subjectivity=sentiment["subjectivity"],
                    confidence=sentiment["confidence"],
                    recommendation_signal=sentiment["recommendation_signal"],
                    reliability=sentiment["reliability"],
                    evidence=sentiment["evidence"],
                    is_known_newsletter=target_newsletter_url in self.known_newsletter_urls,
                )
            )

        return [result.as_dict() for result in results]

    def analyze_post(self, post: Dict, project_root: Optional[Path] = None) -> List[Dict]:
        """Analyze one post dict from index.json."""
        content_path = post.get("content_path") or post.get("local_path")
        if not content_path:
            return []

        path = Path(content_path)
        if not path.is_absolute() and project_root is not None:
            path = project_root / path
        if not path.exists():
            return []

        html = path.read_text(encoding="utf-8", errors="ignore")
        return self.analyze_html(html, source_url=post.get("url", ""))


def update_index_with_citation_sentiment(index_path: Path) -> Dict:
    """Analyze all downloaded posts in index.json and persist citation sentiment."""
    index_path = Path(index_path)
    project_root = index_path.parent.parent

    with index_path.open("r", encoding="utf-8") as f:
        index_data = json.load(f)

    newsletters = index_data.get("newsletters", {})
    analyzer = CitationSentimentAnalyzer(newsletters.keys())

    analyzed_posts = 0
    posts_with_citations = 0
    total_citations = 0

    for newsletter_url, newsletter_data in newsletters.items():
        for post in newsletter_data.get("posts", []):
            citations = analyzer.analyze_post(post, project_root=project_root)
            post["citation_sentiment"] = citations
            post["citation_sentiment_summary"] = summarize_citations(citations)
            post["citation_sentiment_analyzed_at"] = datetime.now().isoformat(timespec="seconds")

            analyzed_posts += 1
            total_citations += len(citations)
            if citations:
                posts_with_citations += 1

    index_data["citation_sentiment_metadata"] = {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "analyzed_posts": analyzed_posts,
        "posts_with_citations": posts_with_citations,
        "total_citations": total_citations,
        "description": (
            "Author feedback signals extracted from locally stored HTML links "
            "to other Substack posts/newsletters."
        ),
    }

    with index_path.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    return index_data["citation_sentiment_metadata"]


def summarize_citations(citations: List[Dict]) -> Dict:
    """Aggregate per-post citation sentiment for ranking/recommendation."""
    if not citations:
        return {
            "total": 0,
            "supportive": 0,
            "critical": 0,
            "neutral": 0,
            "average_polarity": 0.0,
            "average_recommendation_signal": 0.0,
        }

    counts = {"supportive": 0, "critical": 0, "neutral": 0}
    polarity_sum = 0.0
    signal_sum = 0.0
    for citation in citations:
        label = citation.get("sentiment", "neutral")
        counts[label] = counts.get(label, 0) + 1
        polarity_sum += float(citation.get("polarity", 0.0))
        signal_sum += float(citation.get("recommendation_signal", 0.0))

    total = len(citations)
    return {
        "total": total,
        "supportive": counts.get("supportive", 0),
        "critical": counts.get("critical", 0),
        "neutral": counts.get("neutral", 0),
        "average_polarity": round(polarity_sum / total, 4),
        "average_recommendation_signal": round(signal_sum / total, 4),
    }


def score_sentiment(text: str) -> Dict:
    """Backward-compatible wrapper for author stance scoring."""
    return score_author_stance(text)


def score_author_stance(text: str, anchor_text: str = "") -> Dict:
    """Score the author's stance toward the cited post, not generic sentiment.

    The scorer is intentionally conservative: generic emotional language is not
    enough. It looks for evaluative cue phrases near the citation and returns
    low confidence when evidence is sparse or mostly neutral.
    """
    clean_text = normalize_text(text)
    if not clean_text:
        return stance_result("neutral", 0.0, 0.0, 0.0, 0.0, "low", [])

    clauses = split_evidence_clauses(clean_text)
    weighted_score = 0.0
    weighted_abs = 0.0
    evidence: List[str] = []

    anchor_index = find_anchor_clause_index(clauses, anchor_text)

    for index, clause in enumerate(clauses):
        clause_weight = clause_position_weight(index, clauses, anchor_index)
        if HEDGE_RE.search(clause):
            clause_weight *= 0.75

        score, clause_evidence = score_clause(clause)
        if not clause_evidence:
            continue

        weighted_score += score * clause_weight
        weighted_abs += abs(score) * clause_weight
        evidence.extend(clause_evidence)

    if weighted_abs == 0:
        reliability = "low"
        confidence = 0.0
        if NEUTRAL_CITATION_RE.search(clean_text):
            evidence.append("neutral citation/reference language")
        return stance_result("neutral", 0.0, 0.0, confidence, 0.0, reliability, evidence)

    polarity = max(-1.0, min(1.0, weighted_score / max(weighted_abs, 1.0)))
    subjectivity = min(1.0, weighted_abs / 3.0)
    evidence_count = len(evidence)
    confidence = calculate_stance_confidence(
        polarity=polarity,
        subjectivity=subjectivity,
        evidence_count=evidence_count,
        weighted_abs=weighted_abs,
        text=clean_text,
    )

    if polarity >= 0.15:
        label = "supportive"
    elif polarity <= -0.15:
        label = "critical"
    else:
        label = "neutral"

    reliability = reliability_label(confidence, evidence_count)
    recommendation_signal = round(polarity * confidence, 4)
    return stance_result(
        label,
        round(polarity, 4),
        round(subjectivity, 4),
        confidence,
        recommendation_signal,
        reliability,
        evidence[:6],
    )


def extract_link_context(link, anchor_text: str, context_window: int = 2) -> str:
    """Extract nearby prose around a citation link."""
    parent = link.find_parent()
    while parent and len(parent.get_text(" ", strip=True)) < 120:
        parent = parent.find_parent()
    if not parent:
        return ""

    full_text = collapse_whitespace(parent.get_text(" ", strip=True))
    if not full_text:
        return ""

    sentences = split_sentences(full_text)
    if not sentences:
        return full_text[:500]

    anchor_idx = -1
    if anchor_text:
        anchor_idx = next((i for i, sentence in enumerate(sentences) if anchor_text in sentence), -1)

    if anchor_idx == -1:
        return full_text[:500]

    start = max(0, anchor_idx - context_window)
    end = min(len(sentences), anchor_idx + context_window + 1)
    return collapse_whitespace(" ".join(sentences[start:end]))


def extract_plain_text_context(text: str, anchor_text: str, context_window: int = 2) -> str:
    """Extract context around anchor text from plain text fallback parsing."""
    sentences = split_sentences(text)
    if not sentences:
        return text[:500]
    anchor_idx = -1
    if anchor_text:
        anchor_idx = next((i for i, sentence in enumerate(sentences) if anchor_text in sentence), -1)
    if anchor_idx == -1:
        return text[:500]
    start = max(0, anchor_idx - context_window)
    end = min(len(sentences), anchor_idx + context_window + 1)
    return collapse_whitespace(" ".join(sentences[start:end]))


def score_sentiment_with_lexicon(text: str) -> tuple[float, float]:
    """Small fallback scorer retained for callers that need numeric polarity."""
    result = score_author_stance(text)
    return result["polarity"], result["subjectivity"]


def score_clause(clause: str) -> tuple[float, List[str]]:
    """Score one evidence clause and return human-readable evidence labels."""
    score = 0.0
    evidence: List[str] = []

    for pattern, weight, label in SUPPORTIVE_PATTERNS + CRITICAL_PATTERNS:
        for match in pattern.finditer(clause):
            negated = has_local_negation(clause, match.start())
            adjusted_weight = -weight if negated else weight
            score += adjusted_weight
            direction = "supportive" if adjusted_weight > 0 else "critical"
            evidence_label = f"negated {label}" if negated else label
            evidence.append(f"{direction}: {evidence_label} ({match.group(0)})")

    # Generic evaluative words are more reliable when attached to a citation target.
    if evidence and not EVALUATION_TARGET_RE.search(clause):
        score *= 0.65

    return score, evidence


def split_evidence_clauses(text: str) -> List[str]:
    """Split context into manageable clauses while preserving contrast markers."""
    sentences = split_sentences(text)
    clauses: List[str] = []
    for sentence in sentences:
        parts = re.split(r"([,;:])", sentence)
        current = ""
        for part in parts:
            current += part
            if part in {",", ";", ":"}:
                if current.strip():
                    clauses.append(current.strip())
                current = ""
        if current.strip():
            clauses.append(current.strip())
    return clauses or [text]


def find_anchor_clause_index(clauses: List[str], anchor_text: str = "") -> Optional[int]:
    if not anchor_text:
        return None
    return next((i for i, clause in enumerate(clauses) if anchor_text in clause), None)


def clause_position_weight(index: int, clauses: List[str], anchor_index: Optional[int]) -> float:
    """Weight clauses near/after contrast words more heavily."""
    clause = clauses[index]
    if anchor_index is None:
        weight = 0.8
    else:
        distance = abs(index - anchor_index)
        if distance == 0:
            weight = 1.2
        elif distance == 1:
            weight = 0.55
        elif distance == 2:
            weight = 0.25
        else:
            weight = 0.1

    if index > 0 and CONTRAST_RE.search(clauses[index - 1]):
        weight *= 1.15
    if CONTRAST_RE.search(clause):
        weight *= 1.8
        if anchor_index is not None and abs(index - anchor_index) == 1:
            weight = max(weight, 0.95)
    if index >= len(clauses) - 1:
        weight *= 1.02
    return weight


def has_local_negation(text: str, match_start: int) -> bool:
    """Detect short-range negation before an evaluative phrase."""
    prefix = text[max(0, match_start - 45):match_start]
    return bool(NEGATION_RE.search(prefix))


def calculate_stance_confidence(
    polarity: float,
    subjectivity: float,
    evidence_count: int,
    weighted_abs: float,
    text: str,
) -> float:
    """Estimate how much the recommender should trust this stance signal."""
    evidence_factor = min(1.0, evidence_count / 3.0)
    strength_factor = min(1.0, weighted_abs / 2.5)
    confidence = (
        (abs(polarity) * 0.3)
        + (subjectivity * 0.2)
        + (evidence_factor * 0.2)
        + (strength_factor * 0.3)
    )
    if HEDGE_RE.search(text):
        confidence *= 0.85
    if CONTRAST_RE.search(text) and evidence_count < 2:
        confidence *= 0.85
    return round(min(1.0, confidence), 4)


def reliability_label(confidence: float, evidence_count: int) -> str:
    if confidence >= 0.65 and evidence_count >= 2:
        return "high"
    if confidence >= 0.35:
        return "medium"
    return "low"


def stance_result(
    label: str,
    polarity: float,
    subjectivity: float,
    confidence: float,
    recommendation_signal: float,
    reliability: str,
    evidence: List[str],
) -> Dict:
    return {
        "label": label,
        "polarity": polarity,
        "subjectivity": subjectivity,
        "confidence": confidence,
        "recommendation_signal": recommendation_signal,
        "reliability": reliability,
        "evidence": evidence,
    }


def normalize_text(text: str) -> str:
    return collapse_whitespace(unescape(text).replace("\u2019", "'").replace("\u2018", "'"))


def split_sentences(text: str) -> List[str]:
    """Small dependency-free sentence splitter good enough for citation context."""
    return [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(text) if sentence.strip()]


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_tags(html: str) -> str:
    return TAG_RE.sub(" ", html)


def is_substack_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return bool(parsed.scheme in {"http", "https"} and SUBSTACK_HOST_RE.search(host))


def is_substack_post_url(url: str) -> bool:
    """Return True only for actual Substack post links, not subscribe/admin pages."""
    parsed = urlparse(url)
    return is_substack_url(url) and bool(SUBSTACK_POST_PATH_RE.match(parsed.path))


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(query="", fragment="")
    path = normalized.path.rstrip("/")
    normalized = normalized._replace(path=path)
    return urlunparse(normalized)


def normalize_newsletter_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return urlunparse((parsed.scheme, parsed.netloc.lower(), "", "", "", ""))
