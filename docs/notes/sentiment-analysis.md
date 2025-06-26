
"""
NOTES ON VERSIONS & ISSUES (not complete)
===========================

CURRENT VERSION: GEMINI API (Version 4)
- Uses Google Gemini API (model: gemini-pro) via official endpoint.
- Requires:
    - Environment variable `GEMINI_API_KEY` to be set.
    - API must be enabled in Google Cloud Console.
- Pros:
    - Most accurate results so far.
    - Returns YAML with sentiment, score, and confidence.
- Issues faced:
    - API key error (`API_KEY_INVALID`) due to forgetting to enable the API.
    - Required enabling billing (free tier still applies). Have to confirm if want to continue before enabling billing.

PREVIOUS VERSIONS:
---------------------

Version 3: LLaMA/Mistral Local Model
- Used `llama_cpp` to load `mistral.gguf` locally.
- Constructed prompt, stopped with `\n\n` or `</end>`.
- Used regex-based cleanup before YAML parsing.
- Pros:
    - Fully offline, no token usage.
- Issues:
    - Very slow inference.
    - Crashed Mac due to memory/CPU limits.
    - YAML parsing unreliable if model hallucinated formatting.

Version 2: TextBlob + Sentence Context
- Extracted context using `sent_tokenize` and filtered quotes.
- Scored with TextBlob polarity.
- Pros:
    - Fast, dependency-light.
    - Better context due to sentence-framing.
- Issues:
    - Weak semantic accuracy (TextBlob = shallow sentiment).
    - Blockquotes/quotes still introduced noise sometimes.

Version 1: TextBlob + Character Window
- Used 600-character context window around anchor text.
- Simple `TextBlob(text).sentiment.polarity` classification.
- Pros:
    - First functional prototype.
- Issues:
    - Context too arbitrary.
    - Often missed nuance or pulled in irrelevant content.

"""
