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
from pathlib import Path
from typing import Dict, Iterable, List, Optional
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
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
ANCHOR_RE = re.compile(
    r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<text>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
SUPPORTIVE_WORDS = {
    "careful",
    "excellent",
    "great",
    "helpful",
    "insightful",
    "persuasive",
    "recommend",
    "smart",
    "strong",
    "useful",
}
CRITICAL_WORDS = {
    "bad",
    "careless",
    "flawed",
    "misleading",
    "poor",
    "shallow",
    "weak",
    "wrong",
}


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
            if not is_substack_url(target_url):
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
            sentiment = score_sentiment(context)
            seen_targets.add(target_url)
            results.append(
                CitationAnalysisResult(
                    target_url=target_url,
                    target_newsletter_url=target_newsletter_url,
                    target_domain=urlparse(target_newsletter_url).netloc,
                    anchor_text=anchor_text[:160],
                    context=context[:500],
                    sentiment=sentiment["label"],
                    polarity=sentiment["polarity"],
                    subjectivity=sentiment["subjectivity"],
                    confidence=sentiment["confidence"],
                    recommendation_signal=sentiment["recommendation_signal"],
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
            if not is_substack_url(target_url):
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
            sentiment = score_sentiment(context)
            seen_targets.add(target_url)
            results.append(
                CitationAnalysisResult(
                    target_url=target_url,
                    target_newsletter_url=target_newsletter_url,
                    target_domain=urlparse(target_newsletter_url).netloc,
                    anchor_text=anchor_text[:160],
                    context=context[:500],
                    sentiment=sentiment["label"],
                    polarity=sentiment["polarity"],
                    subjectivity=sentiment["subjectivity"],
                    confidence=sentiment["confidence"],
                    recommendation_signal=sentiment["recommendation_signal"],
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
    """Score context text and map it to author feedback labels."""
    if TextBlob is not None:
        blob = TextBlob(text)
        polarity = round(blob.sentiment.polarity, 4)
        subjectivity = round(blob.sentiment.subjectivity, 4)
    else:
        polarity, subjectivity = score_sentiment_with_lexicon(text)

    if polarity >= 0.15:
        label = "supportive"
    elif polarity <= -0.1:
        label = "critical"
    else:
        label = "neutral"

    confidence = round(min(1.0, abs(polarity) + (subjectivity * 0.25)), 4)
    recommendation_signal = round(polarity * confidence, 4)
    return {
        "label": label,
        "polarity": polarity,
        "subjectivity": subjectivity,
        "confidence": confidence,
        "recommendation_signal": recommendation_signal,
    }


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
    """Small fallback scorer for environments without TextBlob."""
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return 0.0, 0.0

    supportive = sum(1 for word in words if word in SUPPORTIVE_WORDS)
    critical = sum(1 for word in words if word in CRITICAL_WORDS)
    signal_words = supportive + critical
    if signal_words == 0:
        return 0.0, 0.0

    polarity = (supportive - critical) / max(signal_words, 1)
    subjectivity = min(1.0, signal_words / max(len(words) * 0.15, 1))
    return round(polarity, 4), round(subjectivity, 4)


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


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(query="", fragment="")
    path = normalized.path.rstrip("/")
    normalized = normalized._replace(path=path)
    return urlunparse(normalized)


def normalize_newsletter_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return urlunparse((parsed.scheme, parsed.netloc.lower(), "", "", "", ""))
