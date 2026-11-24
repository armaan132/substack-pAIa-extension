#!/usr/bin/env node
/* Daily Briefing pAIa — federated-learning prototype demo (Stage 2).
 *
 * Simulates three on-device profiles ("clients"), each with its own private
 * feedback, running one round of Federated Averaging. It prints what each client
 * shares (only term weights — never feedback), the averaged global model, and
 * proof that knowledge crossed between clients: a topic a client never engaged
 * with locally becomes recommendable to it after the round.
 *
 * No network, no data leaves the device. Run: node scripts/federated-demo.js
 */
"use strict";
const { PaiaTopic } = require("../topic.js");
const { PaiaFederated } = require("../federated.js");
const { PaiaEngine } = require("../engine.js");

const like = { read: false, like: true, hide: false, notint: false };
const weightOf = (f) => PaiaEngine.weightOf(f, PaiaEngine.WEIGHTS);

// Three clients with distinct, private interests.
const clients = {
  Ava: ["Quantum computing milestone", "Quantum error correction", "Quantum networking advances"],
  Ben: ["Climate policy shift", "Climate adaptation funding", "Carbon capture at scale"],
  Cleo: ["Neuroscience of memory", "Mapping the connectome", "Neural coding explained"],
};

// Each client builds a LOCAL model from its own feedback, then shares an update.
const updates = [];
const locals = {};
for (const [name, titles] of Object.entries(clients)) {
  const posts = titles.map((t, i) => ({ id: name + i, title: t }));
  const feedback = Object.fromEntries(posts.map((p) => [p.id, like]));
  const model = PaiaTopic.buildModel(posts, feedback, weightOf);
  locals[name] = model;
  const update = PaiaFederated.toUpdate(model, model.rated);
  updates.push(update);
  const terms = Object.keys(update.termAff).sort();
  console.log(`\n${name} trains locally on ${model.rated} posts and shares ONLY weights for:`);
  console.log(`   [${terms.join(", ")}]  (samples=${update.samples})`);
  console.log(`   raw feedback shared: NONE  ·  titles shared: NONE`);
}

// Coordinator averages the weight vectors (it never sees any feedback).
const global = PaiaFederated.round(updates);
console.log(`\n── FedAvg over ${global.clients} clients → global model knows ${Object.keys(global.termAff).length} topics ──`);

// Probe: each client meets a FRESH post on a topic another client taught.
const probes = {
  Ava: { title: "New climate modelling breakthrough", topic: "climate (from Ben)" },
  Ben: { title: "A neuroscience study on memory", topic: "neuroscience (from Cleo)" },
  Cleo: { title: "A quantum computing result", topic: "quantum (from Ava)" },
};

console.log("\nKnowledge transfer — score for a topic each client never engaged with locally:");
let allTransferred = true;
for (const [name, probe] of Object.entries(probes)) {
  const localScore = PaiaTopic.score({ title: probe.title }, locals[name]).score;
  const globalScore = PaiaTopic.score({ title: probe.title }, global).score;
  const gained = globalScore > 0 && localScore === 0;
  allTransferred = allTransferred && gained;
  console.log(
    `   ${name.padEnd(5)} "${probe.title}"\n` +
      `        local-only: ${localScore.toFixed(2)}  →  after federation: ${globalScore.toFixed(2)}` +
      `   [${probe.topic}] ${gained ? "✓ gained" : "—"}`
  );
}

console.log(
  `\nResult: ${allTransferred ? "✓ every client gained a topic from the others" : "partial transfer"} — ` +
    `via shared weights alone, with no feedback ever leaving a device.\n`
);
process.exit(allTransferred ? 0 : 1);
