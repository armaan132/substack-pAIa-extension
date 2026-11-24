/* Daily Briefing pAIa — federated coordinator (Stage 3 prototype).
 *
 * A minimal, dependency-free HTTP server that runs one real round of Federated
 * Averaging across networked clients. Each client POSTs only its learned term
 * weights (never its data); /model returns the FedAvg global model. This is the
 * networked version of the Stage 2 simulation and reuses the SAME aggregation
 * math (federated.js), so client and server can't drift apart.
 *
 * Prototype scope / safety:
 *  - binds to 127.0.0.1 by default (not exposed to the network),
 *  - in-memory only (no disk, no eval, no external code),
 *  - validates and size-caps every request,
 *  - exchanges JSON numbers only — never executable code.
 * It is NOT shipped inside the extension. Deploying it to real users would
 * require authentication, abuse limits, and the privacy-policy/host-permission
 * changes noted in the Stage 3 docs.
 */
"use strict";
const http = require("http");
const { PaiaFederated } = require("../federated.js");

const MAX_BODY = 512 * 1024; // 512 KB per update — generous for a weight vector
const MAX_TERMS = 10000; // cap vocabulary to bound memory
const MAX_ID = 128;

function sendJson(res, status, obj, origin) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    "Content-Type": "application/json",
    // Prototype CORS: echo the caller's origin so a browser extension can reach
    // a locally-run coordinator. A deployed coordinator would allowlist origins.
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > MAX_BODY) {
        reject(new Error("payload too large"));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

// Accept only a well-formed update: a string id, a finite sample count, and a
// term->finite-number map within the vocabulary cap. Anything else is rejected,
// so a malformed or hostile body can't corrupt the global model.
function validateUpdate(obj) {
  if (!obj || typeof obj !== "object") return "body must be an object";
  if (typeof obj.clientId !== "string" || !obj.clientId || obj.clientId.length > MAX_ID)
    return "clientId must be a non-empty string";
  if (obj.samples != null && (typeof obj.samples !== "number" || !Number.isFinite(obj.samples) || obj.samples < 0))
    return "samples must be a non-negative number";
  if (!obj.termAff || typeof obj.termAff !== "object") return "termAff must be an object";
  const terms = Object.keys(obj.termAff);
  if (terms.length > MAX_TERMS) return "too many terms";
  for (const t of terms) {
    const v = obj.termAff[t];
    if (typeof v !== "number" || !Number.isFinite(v)) return "termAff values must be finite numbers";
  }
  return null; // valid
}

function createCoordinator() {
  // clientId -> { termAff, samples }. Latest submission per client wins, so a
  // client re-submitting after more local training replaces its contribution.
  const clients = new Map();
  let round = 1;

  const server = http.createServer(async (req, res) => {
    const origin = req.headers.origin;
    const url = new URL(req.url, "http://localhost");
    try {
      if (req.method === "OPTIONS") return sendJson(res, 204, {}, origin);

      if (req.method === "GET" && url.pathname === "/health") {
        return sendJson(res, 200, { ok: true, round, clients: clients.size }, origin);
      }

      if (req.method === "GET" && url.pathname === "/model") {
        const global = PaiaFederated.aggregate([...clients.values()]);
        return sendJson(res, 200, { round, clients: global.clients, termAff: global.termAff }, origin);
      }

      if (req.method === "POST" && url.pathname === "/submit") {
        let obj;
        try {
          obj = JSON.parse(await readBody(req));
        } catch (e) {
          return sendJson(res, 400, { ok: false, error: "invalid JSON or too large" }, origin);
        }
        const err = validateUpdate(obj);
        if (err) return sendJson(res, 400, { ok: false, error: err }, origin);
        clients.set(obj.clientId, PaiaFederated.toUpdate({ termAff: obj.termAff }, obj.samples));
        return sendJson(res, 200, { ok: true, round, clients: clients.size }, origin);
      }

      if (req.method === "POST" && url.pathname === "/reset") {
        clients.clear();
        round += 1;
        return sendJson(res, 200, { ok: true, round, clients: 0 }, origin);
      }

      return sendJson(res, 404, { ok: false, error: "not found" }, origin);
    } catch (e) {
      return sendJson(res, 500, { ok: false, error: "server error" }, origin);
    }
  });

  return {
    server,
    // Bind to loopback by default; callers pass 0 for an ephemeral test port.
    listen: (port, host) =>
      new Promise((resolve) => server.listen(port || 0, host || "127.0.0.1", () => resolve(server.address()))),
    close: () => new Promise((resolve) => server.close(resolve)),
    _clients: clients,
  };
}

module.exports = { createCoordinator, validateUpdate, MAX_BODY, MAX_TERMS };
