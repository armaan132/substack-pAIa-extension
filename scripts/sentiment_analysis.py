
# scripts/sentiment_analysis.py

# To download newsletter into HTML: 
# curl https://www.astralcodexten.com/p/book-review-selfish-reasons-to-have -o downloaded_post.html
# To run script on dowloaded newsletter: 
# python scripts/sentiment_analysis.py https://www.astralcodexten.com/p/book-review-selfish-reasons-to-have downloaded_post.html


from bs4 import BeautifulSoup
from textblob import TextBlob
import re
import yaml
import sys
import nltk
import requests
from nltk.tokenize import sent_tokenize
from urllib.parse import urlparse

nltk.download('punkt')

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
    print(f"{'✅' if title_tag else '❌'} Found title: {title}")

    content = soup.find("div", attrs={"data-testid": "post-content"}) or soup.find("article") or soup.body
    if not content:
        print("❌ Could not find post content.")
        return {"title": title, "content": None, "text": "", "links": []}

    links = []
    for link in content.find_all("a", href=True):
        href = link['href']
        if "substack.com" in href:
            links.append({
                "url": href,
                "text": link.get_text(strip=True),
                "html_element": str(link)
            })

    print(f"🔗 Found {len(links)} substack links")
    return {"title": title, "content": content, "links": links}


def extract_context(content, links, num_sentences=2):
    enriched = []
    seen_urls = set()

    for link in links:
        if link["url"] in seen_urls:
            continue
        seen_urls.add(link["url"])

        anchor_text = link.get("text", "").strip()
        if not anchor_text:
            continue

        anchor = content.find("a", href=link["url"])
        if anchor:
            parent = anchor.find_parent()
            while parent and len(parent.get_text(strip=True)) < 100:
                parent = parent.find_parent()
            if not parent:
                continue

            full_text = parent.get_text(" ", strip=True)
            sentences = sent_tokenize(full_text)
            anchor_idx = next((i for i, s in enumerate(sentences) if anchor_text in s), -1)

            if anchor_idx == -1:
                context = full_text.strip()
            else:
                start = max(0, anchor_idx - num_sentences)
                end = min(len(sentences), anchor_idx + num_sentences + 1)
                context = " ".join(sentences[start:end])

            # 🧼 Remove sentences that look like blockquotes or inline quotes
            raw_sentences = sent_tokenize(context)
            filtered_sentences = [
                s for s in raw_sentences
                if not s.strip().startswith((">", "“", '"')) and not s.strip().endswith('"')
            ]
            filtered_context = " ".join(filtered_sentences).strip()
            context = filtered_context  # replace with filtered version

            # 🧪 Optional debug output
            # print(f"\n🔍 Original context:\n{context}")
            # print(f"🧽 Filtered context:\n{filtered_context}")

            enriched.append({
                "url": link["url"],
                "text": anchor_text,
                "context": context
            })

    print(f"🧠 Context-extracted links: {len(enriched)}")
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


def fetch_title_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "Unknown Title"
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("h1")
        return title_tag.get_text(strip=True) if title_tag else "Unknown Title"
    except Exception as e:
        print(f"⚠️ Failed to fetch title from {url}: {e}")
        return "Unknown Title"


def generate_graph(url, html):
    parsed = parse_html(html)
    print(f"🔍 Total parsed links: {len(parsed['links'])}")
    context_links = extract_context(parsed["content"], parsed["links"])
    
    analyzed = []
    for link in context_links:
        analysis_text = link['context']
        sentiment = sentiment_analysis(analysis_text)
        
        # 🪓 Lowered threshold from 0.2 → 0.05 for debugging
        if sentiment["confidence"] < 0.05:
            print(f"⚠️ Skipping low-confidence sentiment: {sentiment} for {link['url']}")
            continue

        print(f"📌 Sentiment for: {link['url']} | score: {sentiment['score']} | context len: {len(analysis_text)}")
        link['sentiment'] = sentiment
        analyzed.append(link)

    title_cache = {}

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
        if link["url"] in title_cache:
            target_title = title_cache[link["url"]]
        else:
            target_title = fetch_title_from_url(link["url"])
            title_cache[link["url"]] = target_title

        citation = {
            "target": link["url"],
            "metadata": {
                "target_title": target_title,
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
