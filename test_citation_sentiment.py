import json
from pathlib import Path

from src.analysis.citation_sentiment import (
    CitationSentimentAnalyzer,
    score_sentiment,
    summarize_citations,
    update_index_with_citation_sentiment,
)


def test_analyze_html_extracts_author_feedback():
    html = """
    <html><body><article>
      <p>This is a great and careful post by
      <a href="https://target.substack.com/p/smart-post?utm=1">Target Post</a>.
      I strongly recommend it because the evidence is excellent.</p>
    </article></body></html>
    """

    analyzer = CitationSentimentAnalyzer(["https://target.substack.com"])
    citations = analyzer.analyze_html(html, source_url="https://source.substack.com/p/source")

    assert len(citations) == 1
    assert citations[0]["target_url"] == "https://target.substack.com/p/smart-post"
    assert citations[0]["target_newsletter_url"] == "https://target.substack.com"
    assert citations[0]["sentiment"] == "supportive"
    assert citations[0]["is_known_newsletter"] is True
    assert citations[0]["recommendation_signal"] > 0


def test_score_sentiment_labels_critical_context():
    result = score_sentiment("This argument is weak, careless, and deeply misleading.")

    assert result["label"] == "critical"
    assert result["polarity"] < 0
    assert result["recommendation_signal"] < 0


def test_summarize_citations_aggregates_for_recommendations():
    summary = summarize_citations(
        [
            {"sentiment": "supportive", "polarity": 0.4, "recommendation_signal": 0.2},
            {"sentiment": "critical", "polarity": -0.2, "recommendation_signal": -0.05},
        ]
    )

    assert summary["total"] == 2
    assert summary["supportive"] == 1
    assert summary["critical"] == 1
    assert summary["average_recommendation_signal"] == 0.075


def test_update_index_with_citation_sentiment_persists_fields(tmp_path):
    content_dir = tmp_path / "data" / "content" / "source"
    content_dir.mkdir(parents=True)
    html_path = content_dir / "post.html"
    html_path.write_text(
        """
        <html><body><article>
          <p>I found this excellent essay from
          <a href="https://target.substack.com/p/referenced">another author</a>
          useful and persuasive.</p>
        </article></body></html>
        """,
        encoding="utf-8",
    )

    index_path = tmp_path / "data" / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "newsletters": {
                    "https://source.substack.com": {
                        "name": "Source",
                        "posts": [
                            {
                                "title": "Source Post",
                                "url": "https://source.substack.com/p/post",
                                "content_path": str(html_path),
                            }
                        ],
                    },
                    "https://target.substack.com": {
                        "name": "Target",
                        "posts": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = update_index_with_citation_sentiment(index_path)
    updated = json.loads(index_path.read_text(encoding="utf-8"))
    post = updated["newsletters"]["https://source.substack.com"]["posts"][0]

    assert metadata["analyzed_posts"] == 1
    assert metadata["total_citations"] == 1
    assert post["citation_sentiment"][0]["is_known_newsletter"] is True
    assert post["citation_sentiment_summary"]["total"] == 1

