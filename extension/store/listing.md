# Chrome Web Store listing — copy & answers

Everything you paste into the Web Store developer dashboard. Fields map to the
"Store listing", "Privacy practices", and "Package" tabs.

---

## Store listing tab

**Name**
```
Daily Briefing pAIa
```

**Summary** (max 132 chars)
```
Re-rank your Substack feed by your own likes, reads, and hides. Fully on-device — nothing leaves your browser.
```

**Category**
```
Productivity
```

**Language**
```
English (United States)
```

**Detailed description**
```
Daily Briefing pAIa puts you in control of your Substack reading feed.

Substack shows posts in the order it chooses. This extension re-ranks that feed
using signals only you provide — the posts you like, read, mark "not interesting,"
or hide. Over time your feed floats the writers and publications you actually care
about to the top.

HOW IT WORKS
• A small bar appears on each post in your Substack inbox: like, mark read,
  not interesting, and hide.
• Your feedback builds a per-publication and per-author "affinity" score.
• The feed is re-ranked in place — liked sources rise, ignored ones fall.
• Hover any post's score to see exactly why it ranks where it does.

PRIVATE BY DESIGN
• Everything runs on your device. Your feedback and ranking are stored locally
  in your browser (chrome.storage) and are never sent anywhere.
• No account. No server. No tracking. No other users' data.
• Export or import your signals as a JSON file anytime.

MADE TO STAY OUT OF THE WAY
• Auto-marks a post read when you open it (toggleable).
• Hide posts you don't want; restore them anytime.
• Tune how much each action counts from the options page.
• Keyboard-accessible controls and reduced-motion support.

Open your Substack inbox and the controls appear. That's it.

Daily Briefing pAIa is not affiliated with or endorsed by Substack.
```

**Single purpose** (required statement)
```
This extension has one purpose: to re-rank the user's Substack reader feed
according to feedback the user provides about posts (like, read, not interesting,
hide), using only data stored locally on the user's own device.
```

---

## Privacy practices tab

**Permission justifications**

`storage`
```
Used to save the user's own feedback (likes, reads, not-interesting, hides) and
settings locally on their device, so the feed can be re-ranked consistently
across page loads and sessions. No data is transmitted off the device.
```

`host_permissions` — `*://*.substack.com/*`
```
The extension only runs on Substack pages. It needs access to Substack in order
to read the visible list of posts in the feed and to inject the ranking controls
and scores. It does not read or modify any site other than Substack, and makes no
network requests of its own.
```

**Remote code**: No, this extension does not use remote code.
(All logic ships in the package; MV3 CSP is `script-src 'self'`.)

**Data collection disclosures** — check NONE of the data-type boxes. Then affirm:
- ☑ I do not sell or transfer user data to third parties (outside approved use cases)
- ☑ I do not use or transfer user data for purposes unrelated to the item's single purpose
- ☑ I do not use or transfer user data to determine creditworthiness or for lending

Rationale to keep on file: the extension collects **no** user data in the Web
Store sense — all feedback stays in local browser storage and is never sent to
any server, including ours (there is no server).

**Privacy policy URL**: (hosted on GitHub Pages)
```
https://ashrayg09.github.io/paia-privacy/
```

---

## Package tab

Upload the zip produced by `scripts/build-zip.sh` (see STORE-SUBMISSION.md).
It contains only the files the extension runs — no tests, node_modules, or docs.

---

## Assets checklist

- [x] Store icon 128×128 — `icons/icon128.png`
- [ ] At least 1 screenshot, 1280×800 (or 640×400) — see `store/screenshots/`
- [ ] Small promo tile 440×280 (optional but recommended)
- [ ] Privacy policy hosted at a public URL
