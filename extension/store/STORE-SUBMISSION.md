# Chrome Web Store submission — step by step

Everything needed to publish **Daily Briefing pAIa**. The copy lives in
[`listing.md`](listing.md); this is the checklist and process.

Steps marked **(you)** need your Google account or personal details and can't be
automated. Everything else is prepared in this folder.

---

## 0. One-time prerequisites (you)

- [ ] A Google account for the developer.
- [ ] Register as a Chrome Web Store developer — **one-time $5 USD fee** at
      https://chrome.google.com/webstore/devconsole
- [ ] Fill in the two placeholders first:
  - `store/privacy.html` → replace `[your contact email]`
  - `store/listing.md` → replace the privacy-policy URL once hosted (next step)

## 1. Host the privacy policy (you)

The Web Store requires a public privacy-policy URL. `store/privacy.html` is ready
to host. Easiest option — GitHub Pages:

1. Put `privacy.html` in a **public** repo (or enable Pages on one).
2. Enable **Settings → Pages** → deploy from the branch.
3. Your URL will look like `https://<user>.github.io/<repo>/privacy.html`.
4. Paste that URL into the listing's "Privacy policy URL" field.

(Any public host works — a gist rendered via htmlpreview, Netlify drop, etc.)

## 2. Build the package

```sh
bash scripts/build-zip.sh
```

Produces `store/daily-briefing-paia.zip` — only the 15 files the extension runs
(no tests, node_modules, docs, or dev config). Re-run this after any code change.

## 3. Final pre-flight (already ✅, re-check after edits)

```sh
npm test          # 24/24 green
npm run lint      # no remote code / eval; syntax ok
```

- [ ] Load-unpacked smoke test on a clean Chrome profile, open `substack.com/inbox`.
- [ ] Version in `manifest.json` is correct (each submission needs a higher version).

## 4. Create the item & upload (you)

1. Developer Dashboard → **Add new item**.
2. Upload `store/daily-briefing-paia.zip`.
3. **Store listing** tab — paste from `listing.md`: name, summary, description,
   category (Productivity), language.
4. **Graphic assets**:
   - Store icon: `icons/icon128.png`
   - Screenshots (1280×800): `store/screenshots/1-inbox.png`,
     `2-popup.png`, `3-options.png`
   - (Optional) small promo tile 440×280.
5. **Privacy practices** tab — paste from `listing.md`:
   - Single purpose statement
   - Permission justifications (`storage`, host access)
   - Remote code: **No**
   - Data collection: check **nothing**; affirm the three data-use statements
   - Privacy policy URL (from step 1)

## 5. Submit (you)

- [ ] Click **Submit for review**.
- [ ] Review typically takes a few days. Watch the developer email for the result.

## 6. After approval

- [ ] Share the store link.
- [ ] For updates: bump `manifest.json` version → `bash scripts/build-zip.sh` →
      upload the new zip → submit.

---

## What's in this folder

| File | Purpose |
|------|---------|
| `listing.md` | All dashboard copy + permission justifications + single purpose |
| `privacy.html` | Privacy policy, ready to host |
| `STORE-SUBMISSION.md` | This guide |
| `daily-briefing-paia.zip` | The uploadable package (from build-zip.sh) |
| `screenshots/` | 1280×800 store screenshots |
| `shots/` | The seeded pages used to render the screenshots |

## Notes on review-readiness

- **Single purpose** is clean: re-rank the user's Substack feed from their own
  on-device feedback.
- **Minimal permissions**: `storage` + `*.substack.com` only. No `tabs`, no
  `<all_urls>`, no remote hosts.
- **No remote code**: enforced by MV3 CSP (`script-src 'self'`) and checked by
  `scripts/check-no-remote-code.js`.
- **No data collection**: nothing leaves the device; there is no server.
- These are the usual rejection triggers, and all are addressed — but reviewers
  can still ask questions; answer using the rationale in `listing.md`.
