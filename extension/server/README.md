# Federated coordinator (Stage 3 prototype)

A minimal, dependency-free Federated Averaging (FedAvg) coordinator for the
pAIa topic model. It is the **networked** version of the Stage 2 simulation and
reuses the same aggregation math (`../federated.js`), so client and server can't
drift apart.

## What it does

Clients train a topic model locally (`topic.js`), then exchange **only learned
term weights** with the coordinator — never feedback, post IDs, or titles.

```
client ──POST /submit {clientId, termAff, samples}──▶ coordinator
client ◀──────── GET /model {termAff} (FedAvg) ────── coordinator
```

| Route | Method | Purpose |
|-------|--------|---------|
| `/health` | GET | `{ ok, round, clients }` |
| `/submit` | POST | store one client's weight update (latest-per-client wins) |
| `/model`  | GET  | the FedAvg global model, shaped for `PaiaTopic.score` |
| `/reset`  | POST | clear the round (dev/demo only) |

## Run it

```bash
node scripts/fl-network-demo.js      # starts a coordinator + 3 simulated clients
npm test                             # tests/fl-network.test.js drives it over real HTTP
```

## Prototype safety (what's already true)

- Binds to `127.0.0.1` by default — not exposed to the network.
- In-memory only: no disk, no `eval`, no external code; exchanges JSON numbers.
- Every request is validated and size-capped (`validateUpdate`, `MAX_BODY`,
  `MAX_TERMS`); malformed or hostile bodies are rejected with `400` and ignored.
- **Not shipped inside the extension.** It is not in `manifest.json` or the
  store zip, and no content script or service worker calls it.

## What shipping this to real users would require (NOT done yet)

This is the one stage that changes the extension's privacy posture, so it is
deliberately left unshipped until these are in place:

1. **Privacy-policy + store-listing update.** The current promise is "nothing
   leaves your device." Real FL sends *model updates* (not raw data), so the
   listing must say so, e.g.: *"Your reading data never leaves your device. The
   optional federated mode shares only anonymized model weights — never your
   content."* Raw feedback still never leaves, which is FL's actual guarantee.
2. **Opt-in, off by default.** A setting (`federated: false`) plus a clear
   first-run explanation. No background network calls unless enabled.
3. **A host permission** for the coordinator's exact origin (e.g.
   `https://fl.example.org/*`), justified in the submission.
4. **Server hardening**: authentication / rate limiting / abuse protection,
   per-round differential-privacy noise on the weights, a secure-aggregation or
   trimmed-mean step so one client can't skew or probe the global model, TLS,
   and a retention policy. In-memory latest-wins is a prototype, not production.
5. **Governance.** Because a deployed coordinator receives data from many users,
   it needs a named operator and an age/consent story — to be decided with
   Prof. Kurz before any public deployment.

Until all of the above exist, keep the coordinator local (loopback) and treat
this as a research prototype.
