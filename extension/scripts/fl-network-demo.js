#!/usr/bin/env node
/* Daily Briefing pAIa — networked federated-learning demo (Stage 3).
 *
 * Starts a real coordinator on 127.0.0.1, then has three clients submit their
 * learned weights OVER HTTP and pull back the averaged global model. Prints what
 * crosses the wire (only weights) and proves knowledge transfer between clients.
 * No data leaves the loopback interface. Run: node scripts/fl-network-demo.js
 */
"use strict";
const { createCoordinator } = require("../server/coordinator.js");
const FLClient = require("../fl-client.js");
const { PaiaTopic } = require("../topic.js");
const { PaiaFederated } = require("../federated.js");
const { PaiaEngine } = require("../engine.js");

const like = { read: false, like: true, hide: false, notint: false };
const weightOf = (f) => PaiaEngine.weightOf(f, PaiaEngine.WEIGHTS);

const clients = {
  Ava: ["Quantum computing milestone", "Quantum error correction"],
  Ben: ["Climate policy shift", "Carbon capture at scale"],
  Cleo: ["Neuroscience of memory", "Mapping the connectome"],
};

function localModel(titles) {
  const posts = titles.map((t, i) => ({ id: i + t, title: t }));
  const feedback = Object.fromEntries(posts.map((p) => [p.id, like]));
  return PaiaTopic.buildModel(posts, feedback, weightOf);
}

(async () => {
  const coord = createCoordinator();
  const addr = await coord.listen(0, "127.0.0.1");
  const baseUrl = `http://127.0.0.1:${addr.port}`;
  console.log(`Coordinator listening on ${baseUrl} (loopback only)\n`);

  const locals = {};
  for (const [name, titles] of Object.entries(clients)) {
    const model = localModel(titles);
    locals[name] = model;
    const update = PaiaFederated.toUpdate(model, model.rated);
    const ack = await FLClient.submitUpdate(baseUrl, name, update);
    console.log(
      `${name} ──POST /submit──> coordinator   ` +
        `(sent ${Object.keys(update.termAff).length} weights, samples=${update.samples}; feedback sent: NONE)` +
        `  → round now has ${ack.clients} client(s)`
    );
  }

  const global = await FLClient.fetchGlobalModel(baseUrl);
  console.log(`\nGET /model → global FedAvg model over ${global.clients} clients, ${Object.keys(global.termAff).length} topics\n`);

  const probes = {
    Ava: { title: "A neuroscience study on memory", from: "Cleo" },
    Ben: { title: "A quantum computing result", from: "Ava" },
    Cleo: { title: "New carbon capture funding", from: "Ben" },
  };
  console.log("Knowledge transfer (score for a topic the client never saw locally):");
  let ok = true;
  for (const [name, probe] of Object.entries(probes)) {
    const local = PaiaTopic.score({ title: probe.title }, locals[name]).score;
    const glob = PaiaTopic.score({ title: probe.title }, global).score;
    const gained = glob > 0 && local === 0;
    ok = ok && gained;
    console.log(
      `   ${name.padEnd(5)} "${probe.title}"  local ${local.toFixed(2)} → global ${glob.toFixed(2)}` +
        `  (learned from ${probe.from}) ${gained ? "✓" : "—"}`
    );
  }
  console.log(`\n${ok ? "✓" : "partial:"} every client gained a topic over the network — weights only, no data shared.`);

  await coord.close();
  process.exit(ok ? 0 : 1);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
