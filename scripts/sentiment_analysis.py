# scripts/sentiment_analysis.py

from bs4 import BeautifulSoup
from textblob import TextBlob
import re
import yaml
import sys
from urllib.parse import urlparse

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Try more flexible title extraction
    title_tag = soup.find("h1")
    if not title_tag:
        print("❌ Could not find <h1> title.")
        title = "Unknown Title"
    else:
        title = title_tag.get_text(strip=True)
        print(f"✅ Found title: {title}")

    # Try standard + fallback for content
    content = soup.find("div", attrs={"data-testid": "post-content"}) or soup.find("article") or soup.body
    if not content:
        print("❌ Could not find post content.")
        return {"title": title, "content": None, "text": "", "links": []}

    full_text = content.get_text(" ", strip=True)

    links = []
    for link in content.find_all("a", href=True):
        href = link['href']
        if "substack.com" in href:
            links.append({
                "url": href,
                "text": link.get_text(strip=True),
                "html_element": str(link)
            })

    print(f"🔗 Found {len(links)} links")

    return {"title": title, "content": content, "text": full_text, "links": links}

def extract_context(content, links, window=200):
    enriched = []
    seen_urls = set()

    for link in links:
        if link["url"] in seen_urls:
            continue
        seen_urls.add(link["url"])

        anchor_text = link.get("text", "").strip()
        if not anchor_text:
            continue  # skip links with no visible text

        anchor = content.find("a", href=link["url"])
        if anchor:
            parent = anchor.find_parent()
            while parent and len(parent.get_text(strip=True)) < 100:
                parent = parent.find_parent()

            if not parent:
                continue

            parent_text = parent.get_text(" ", strip=True)
            anchor_pos = parent_text.find(anchor_text)

            if anchor_pos != -1:
                start = max(0, anchor_pos - window)
                end = min(len(parent_text), anchor_pos + len(anchor_text) + window)
                context = parent_text[start:end]
            else:
                context = parent_text[:window * 2]

            context = re.sub(r"\s+", " ", context)
            enriched.append({
                "url": link["url"],
                "text": anchor_text,
                "context": context
            })

    return enriched


def sentiment_analysis(text):
    score = TextBlob(text).sentiment.polarity
    if score > 0.2:
        category = "favorable"
    elif score < -0.1:
        category = "unfavorable"
    else:
        category = "neutral"
    return {"category": category, "score": score, "confidence": abs(score)}

def extract_name(url):
    parsed = urlparse(url)
    return parsed.netloc.split(".")[0] if parsed.netloc else "unknown"


def generate_graph(url, html):
    parsed = parse_html(html)
    context_links = extract_context(parsed["content"], parsed["links"])
    analyzed = []
    for link in context_links:
        analysis_text = f"{link['text']} {link['context']}"
        sentiment = sentiment_analysis(analysis_text)
        link['sentiment'] = sentiment
        analyzed.append(link)

    graph = {
        "newsletters": [
            {
                "id": url,
                "metadata": {
                    "name": extract_name(url),
                    "title": parsed["title"]
                },
                "citations": []
            }
        ]
    }

    for link in analyzed:
        citation = {
            "target": link["url"],
            "metadata": {
                "sentiment": link["sentiment"]["category"],
                "score": link["sentiment"]["score"],
                "confidence": link["sentiment"]["confidence"],
                "context": link["context"][:200] + "..."
            }
        }
        graph["newsletters"][0]["citations"].append(citation)

    return yaml.dump(graph, sort_keys=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/sentiment_analysis.py <source_url> <html_file>")
        sys.exit(1)

    src_url = sys.argv[1]
    html_path = sys.argv[2]

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    result_yaml = generate_graph(src_url, html)
    name = extract_name(src_url)
    with open(f"newsletter_graph_{name}.yaml", "w") as out:
        out.write(result_yaml)

    print(f"✅ Output written to newsletter_graph_{name}.yaml")
