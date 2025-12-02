/**
 * Tests for the Hashgraph GraphQuerier methods.
 * These tests mirror the Python tests in examples/python/src/test_graph.py
 */

import {
  init,
  createHashgraph,
  createGraphQuerierFromJson,
  type Hashgraph,
  type GraphQuerier,
} from "./wasm";
import * as ed from "@noble/ed25519";

// Peer IDs matching the Rust tests
const ALICE = 1n;
const BOB = 2n;
const CATHY = 3n;
const DAVE = 4n;
const PEERS = [ALICE, BOB, CATHY, DAVE];

interface Keys {
  privateKeys: Map<bigint, Uint8Array>;
  publicKeys: Map<number, Uint8Array>;
}

async function generateKeys(numPeers: number): Promise<Keys> {
  const privateKeys = new Map<bigint, Uint8Array>();
  const publicKeys = new Map<number, Uint8Array>();

  for (let peer = 1; peer <= numPeers; peer++) {
    const privateKey = ed.utils.randomPrivateKey();
    const publicKey = await ed.getPublicKeyAsync(privateKey);
    privateKeys.set(BigInt(peer), privateKey);
    publicKeys.set(peer, publicKey);
  }

  return { privateKeys, publicKeys };
}

async function buildFigure1Hashgraphs(): Promise<Map<bigint, Hashgraph>> {
  const { privateKeys, publicKeys } = await generateKeys(4);
  const hashgraphs = new Map<bigint, Hashgraph>();

  for (const peer of PEERS) {
    hashgraphs.set(peer, createHashgraph(peer, 0n, privateKeys.get(peer)!, publicKeys));
  }

  // Simulate the exchanges from Figure 1
  const exchange = (from: bigint, to: bigint, timestamp: bigint) => {
    const msg = hashgraphs.get(from)!.send();
    hashgraphs.get(to)!.receive(msg, timestamp);
  };

  exchange(DAVE, CATHY, 1n);   // D1 -> C2
  exchange(CATHY, DAVE, 1n);   // C2 -> D2
  exchange(BOB, ALICE, 1n);    // B1 -> A2
  exchange(BOB, CATHY, 2n);    // B1 -> C3
  exchange(ALICE, BOB, 1n);    // A1 -> B2
  exchange(ALICE, BOB, 2n);    // A2 -> B3
  exchange(CATHY, BOB, 3n);    // C3 -> B4
  exchange(DAVE, BOB, 4n);     // D2 -> B5

  return hashgraphs;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}

interface GraphJson {
  total_peers: number;
  events: Record<string, {
    kind: string;
    timestamp: number;
    peer?: number;
    transactions?: string;
    self_parent?: string;
    other_parent?: string;
  }>;
}

function getEventHashesByPeer(graph: GraphQuerier): Map<bigint, Uint8Array[]> {
  const graphJson: GraphJson = JSON.parse(graph.asJson());
  const hashesByPeer = new Map<bigint, [number, Uint8Array][]>();

  for (const [hashHex, event] of Object.entries(graphJson.events)) {
    const peer = graph.creator(hashHex);
    if (!hashesByPeer.has(peer)) hashesByPeer.set(peer, []);
    hashesByPeer.get(peer)!.push([event.timestamp, hexToBytes(hashHex)]);
  }

  const result = new Map<bigint, Uint8Array[]>();
  for (const [peer, events] of hashesByPeer) {
    events.sort((a, b) => a[0] - b[0]);
    result.set(peer, events.map(([, hash]) => hash));
  }
  return result;
}

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

class TestResults {
  passed = 0;
  failed = 0;
  errors: string[] = [];

  check(condition: boolean, message: string): void {
    if (condition) {
      this.passed++;
    } else {
      this.failed++;
      this.errors.push(message);
    }
  }

  summary(): boolean {
    console.log(`\n${"=".repeat(60)}`);
    console.log(`Tests passed: ${this.passed}`);
    console.log(`Tests failed: ${this.failed}`);
    if (this.errors.length > 0) {
      console.log("\nFailures:");
      for (const error of this.errors) console.log(`  - ${error}`);
    }
    console.log("=".repeat(60));
    return this.failed === 0;
  }
}

// Helper to run tests with automatic cleanup
async function withGraph<T>(fn: (graph: GraphQuerier, hashgraphs: Map<bigint, Hashgraph>) => T): Promise<T> {
  const hashgraphs = await buildFigure1Hashgraphs();
  const graph = hashgraphs.get(BOB)!.graph;
  try {
    return fn(graph, hashgraphs);
  } finally {
    graph.free();
    for (const hg of hashgraphs.values()) hg.free();
  }
}

async function testHashgraphFields(results: TestResults): Promise<void> {
  console.log("\n[TEST] Hashgraph fields...");

  const { privateKeys, publicKeys } = await generateKeys(2);
  const hg = createHashgraph(1n, 0n, privateKeys.get(1n)!, publicKeys);

  results.check(hg.id === 1n, "id should be 1n");
  results.check(hg.pendingTransactions.length === 0, "pendingTransactions should be empty");
  results.check(hg.signer.length === 32, "signer should be 32 bytes");
  results.check(bytesToHex(hg.signer) === bytesToHex(privateKeys.get(1n)!), "signer should match private key");
  results.check(hg.verifiers.size === 2, "verifiers should have 2 entries");

  for (const [peerId, pubKey] of hg.verifiers) {
    const peerIdNum = typeof peerId === "bigint" ? Number(peerId) : peerId as number;
    results.check((pubKey as Uint8Array).length === 32, `verifier ${peerId} should be 32 bytes`);
    results.check(bytesToHex(pubKey as Uint8Array) === bytesToHex(publicKeys.get(peerIdNum)!), `verifier ${peerId} should match public key`);
  }

  hg.appendTransaction(new TextEncoder().encode("test transaction"));
  results.check(new TextDecoder().decode(hg.pendingTransactions) === "test transaction", "pendingTransactions should contain appended data");

  console.log("  Fields test completed");
  hg.free();
}

async function testGraphAsJson(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.asJson()...");

  await withGraph((graph) => {
    const parsed: GraphJson = JSON.parse(graph.asJson());

    results.check("total_peers" in parsed, "Graph JSON should have 'total_peers'");
    results.check("events" in parsed, "Graph JSON should have 'events'");
    results.check(parsed.total_peers === 4, "total_peers should be 4");
    results.check(Object.keys(parsed.events).length > 0, "Graph should have events");

    for (const [hashHex, event] of Object.entries(parsed.events)) {
      results.check("kind" in event, `Event ${hashHex.slice(0, 8)}... should have 'kind'`);
      results.check("timestamp" in event, `Event ${hashHex.slice(0, 8)}... should have 'timestamp'`);
      if (event.kind === "initial") {
        results.check("peer" in event, "Initial event should have 'peer'");
      } else if (event.kind === "default") {
        results.check("transactions" in event, "Default event should have 'transactions'");
        results.check("self_parent" in event, "Default event should have 'self_parent'");
        results.check("other_parent" in event, "Default event should have 'other_parent'");
      }
    }
  });

  console.log("  asJson test completed");
}

async function testIsSupermajority(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.isSupermajority()...");

  await withGraph((graph) => {
    // For 4 peers, supermajority means > 2/3 * 4 = 2.67, so at least 3
    results.check(!graph.isSupermajority(0), "0 should not be supermajority");
    results.check(!graph.isSupermajority(1), "1 should not be supermajority");
    results.check(!graph.isSupermajority(2), "2 should not be supermajority");
    results.check(graph.isSupermajority(3), "3 should be supermajority");
    results.check(graph.isSupermajority(4), "4 should be supermajority");
  });

  console.log("  isSupermajority test completed");
}

async function testEventsAsBytes(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.eventsAsBytes()...");

  await withGraph((graph) => {
    const eventBytes = graph.eventsAsBytes();
    results.check(eventBytes.length > 0, "eventsAsBytes should return non-empty bytes");
    results.check(eventBytes instanceof Uint8Array, "eventsAsBytes should return Uint8Array");
  });

  console.log("  eventsAsBytes test completed");
}

async function testLatestEvent(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.latestEvent()...");

  await withGraph((graph) => {
    const latestBob = graph.latestEvent(BOB);
    results.check(latestBob !== undefined, "BOB should have a latest event");

    if (latestBob) {
      results.check(latestBob.length === 32, "latestEvent should return 32-byte hash");
      results.check(latestBob instanceof Uint8Array, "latestEvent should return Uint8Array");
      const event = JSON.parse(graph.getEvent(latestBob));
      results.check(event.kind === "default", "BOB's latest should be a default event");
    }

    results.check(graph.latestEvent(999n) === undefined, "Unknown peer should return undefined");
  });

  console.log("  latestEvent test completed");
}

async function testGetEvent(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.getEvent()...");

  await withGraph((graph) => {
    const graphJson: GraphJson = JSON.parse(graph.asJson());
    const someHashHex = Object.keys(graphJson.events)[0];
    const event = JSON.parse(graph.getEvent(someHashHex));

    results.check("kind" in event, "getEvent should return valid event JSON");
    results.check("timestamp" in event, "Event should have timestamp");
  });

  console.log("  getEvent test completed");
}

async function testCreator(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.creator()...");

  await withGraph((graph) => {
    const graphJson: GraphJson = JSON.parse(graph.asJson());

    for (const [hashHex, event] of Object.entries(graphJson.events)) {
      if (event.kind === "initial") {
        results.check(graph.creator(hashHex) === BigInt(event.peer!), "Creator of initial event should match peer field");
      }
    }
  });

  console.log("  creator test completed");
}

async function testAncestorRelations(results: TestResults): Promise<void> {
  console.log("\n[TEST] Ancestor relations...");

  await withGraph((graph) => {
    const hashesByPeer = getEventHashesByPeer(graph);
    const bobEvents = hashesByPeer.get(BOB);

    if (bobEvents && bobEvents.length >= 2) {
      const [bobFirst, bobLast] = [bobEvents[0], bobEvents[bobEvents.length - 1]];

      // Ancestor tests
      results.check(graph.isAncestor(bobFirst, bobFirst), "Event should be ancestor of itself");
      results.check(graph.isAncestor(bobFirst, bobLast), "First event should be ancestor of last");
      results.check(!graph.isAncestor(bobLast, bobFirst), "Last event should not be ancestor of first");

      // Strict ancestor tests
      results.check(!graph.isStrictAncestor(bobFirst, bobFirst), "Event should not be strict ancestor of itself");
      results.check(graph.isStrictAncestor(bobFirst, bobLast), "First should be strict ancestor of last");

      // Self-ancestor tests
      results.check(graph.isSelfAncestor(bobFirst, bobLast), "First should be self-ancestor of last");
      results.check(!graph.isSelfAncestor(bobLast, bobFirst), "Last should not be self-ancestor of first");
      results.check(!graph.isStrictSelfAncestor(bobFirst, bobFirst), "Event should not be strict self-ancestor of itself");
    }
  });

  console.log("  Ancestor relations test completed");
}

async function testForkDetection(results: TestResults): Promise<void> {
  console.log("\n[TEST] Fork detection...");

  await withGraph((graph) => {
    const hashesByPeer = getEventHashesByPeer(graph);
    const bobEvents = hashesByPeer.get(BOB);

    // Consecutive events from same peer should not be forks
    if (bobEvents && bobEvents.length >= 2) {
      for (let i = 0; i < bobEvents.length - 1; i++) {
        results.check(!graph.isFork(bobEvents[i], bobEvents[i + 1]), "Consecutive events should not be forks");
      }
    }

    // No event should see dishonesty in the honest Figure 1 graph
    const graphJson: GraphJson = JSON.parse(graph.asJson());
    for (const hashHex of Object.keys(graphJson.events).slice(0, 5)) {
      for (const peer of PEERS) {
        results.check(!graph.canSeeDishonesty(hashHex, peer), "No event should see dishonesty in honest graph");
      }
    }
  });

  console.log("  Fork detection test completed");
}

async function testSeesAndStronglySees(results: TestResults): Promise<void> {
  console.log("\n[TEST] Sees and stronglySees...");

  await withGraph((graph) => {
    const hashesByPeer = getEventHashesByPeer(graph);
    const bobEvents = hashesByPeer.get(BOB);

    if (bobEvents && bobEvents.length >= 2) {
      const [bobFirst, bobLast] = [bobEvents[0], bobEvents[bobEvents.length - 1]];
      results.check(graph.sees(bobFirst, bobLast) === graph.isAncestor(bobFirst, bobLast), "In honest graph, sees should equal isAncestor");
    }

    if (bobEvents) {
      const bobLast = bobEvents[bobEvents.length - 1];
      let stronglySeenCount = 0;
      for (const [, events] of hashesByPeer) {
        if (events.length > 0 && graph.stronglySees(events[0], bobLast)) {
          stronglySeenCount++;
        }
      }
      results.check(stronglySeenCount >= 1, `Last event should strongly see at least 1 initial event, saw ${stronglySeenCount}`);
    }
  });

  console.log("  Sees and stronglySees test completed");
}

async function testRound(results: TestResults): Promise<void> {
  console.log("\n[TEST] Round calculation...");

  await withGraph((graph) => {
    const hashesByPeer = getEventHashesByPeer(graph);

    // Initial events should be in round 0
    for (const [peer, events] of hashesByPeer) {
      if (events.length > 0) {
        const eventJson = JSON.parse(graph.getEvent(events[0]));
        if (eventJson.kind === "initial") {
          const roundNum = graph.round(events[0]);
          results.check(roundNum === 0n, `Initial event of peer ${peer} should be in round 0, got ${roundNum}`);
        }
      }
    }

    // Find max round
    let maxRound = 0n;
    for (const [, events] of hashesByPeer) {
      for (const eventHash of events) {
        const roundNum = graph.round(eventHash);
        if (roundNum > maxRound) maxRound = roundNum;
      }
    }

    results.check(maxRound >= 0n, `Max round should be at least 0, got ${maxRound}`);
    console.log(`  Max round found: ${maxRound}`);
  });

  console.log("  Round calculation test completed");
}

async function testWitnesses(results: TestResults): Promise<void> {
  console.log("\n[TEST] Witnesses calculation...");

  await withGraph((graph) => {
    const witnessesR0 = graph.witnesses(0n);
    results.check(witnessesR0.length > 0, "Round 0 should have witnesses");

    for (const witnessHash of witnessesR0) {
      const eventJson = JSON.parse(graph.getEvent(witnessHash));
      results.check(eventJson.kind === "initial", "Round 0 witnesses should be initial events");
    }

    const witnessesR1 = graph.witnesses(1n);
    for (const witnessHash of witnessesR1) {
      results.check(graph.round(witnessHash) === 1n, "Round 1 witnesses should be in round 1");
    }

    console.log(`  Round 0 witnesses: ${witnessesR0.length}`);
    console.log(`  Round 1 witnesses: ${witnessesR1.length}`);
  });

  console.log("  Witnesses calculation test completed");
}

async function testGraphQuerierFromJsonAndAsJson(results: TestResults): Promise<void> {
  console.log("\n[TEST] GraphQuerier.fromJson() and GraphQuerier.asJson()...");

  await withGraph((originalGraph) => {
    const originalJsonStr = originalGraph.asJson();
    const originalParsed: GraphJson = JSON.parse(originalJsonStr);

    const reconstructed = createGraphQuerierFromJson(originalJsonStr);
    const reconstructedParsed: GraphJson = JSON.parse(reconstructed.asJson());

    results.check(reconstructedParsed.total_peers === originalParsed.total_peers, `total_peers should match`);
    results.check(Object.keys(reconstructedParsed.events).length === Object.keys(originalParsed.events).length, `Event count should match`);

    for (const hashHex of Object.keys(originalParsed.events)) {
      results.check(hashHex in reconstructedParsed.events, `Event ${hashHex.slice(0, 8)}... should exist in reconstructed graph`);
    }

    results.check(reconstructed.isSupermajority(3), "Reconstructed graph should recognize 3 as supermajority");
    results.check(!reconstructed.isSupermajority(2), "Reconstructed graph should not recognize 2 as supermajority");
    results.check(reconstructed.latestEvent(BOB) !== undefined, "Reconstructed graph should have BOB's latest event");

    reconstructed.free();
  });

  console.log("  GraphQuerier.fromJson() and GraphQuerier.asJson() test completed");
}

async function testHashgraphAsJson(results: TestResults): Promise<void> {
  console.log("\n[TEST] Hashgraph.asJson()...");

  const hashgraphs = await buildFigure1Hashgraphs();
  const hg = hashgraphs.get(BOB)!;

  hg.appendTransaction(new TextEncoder().encode("test_tx_1"));
  hg.appendTransaction(new TextEncoder().encode("test_tx_2"));

  const parsed = JSON.parse(hg.asJson());

  results.check("id" in parsed, "Hashgraph JSON should have 'id'");
  results.check("pending_transactions" in parsed, "Hashgraph JSON should have 'pending_transactions'");
  results.check("graph" in parsed, "Hashgraph JSON should have 'graph'");
  results.check(parsed.id === Number(BOB), `id should be ${BOB}, got ${parsed.id}`);
  results.check(parsed.pending_transactions !== null, "pending_transactions should not be null");
  results.check(parsed.pending_transactions.length > 0, "pending_transactions should not be empty after appending");

  const graphData = parsed.graph;
  results.check("total_peers" in graphData, "Graph in Hashgraph JSON should have 'total_peers'");
  results.check("events" in graphData, "Graph in Hashgraph JSON should have 'events'");
  results.check(graphData.total_peers === 4, `total_peers should be 4, got ${graphData.total_peers}`);
  results.check(Object.keys(graphData.events).length > 0, "Graph should have events");

  console.log("  Hashgraph.asJson() test completed");
  for (const h of hashgraphs.values()) h.free();
}

async function main(): Promise<number> {
  console.log("=".repeat(60));
  console.log("Hashgraph GraphQuerier Tests");
  console.log("(TypeScript port of examples/python/src/test_graph.py)");
  console.log("=".repeat(60));

  console.log("\nInitializing WASM...");
  await init();
  console.log("WASM initialized successfully!");

  const results = new TestResults();

  try {
    await testHashgraphFields(results);
    await testGraphAsJson(results);
    await testGraphQuerierFromJsonAndAsJson(results);
    await testHashgraphAsJson(results);
    await testIsSupermajority(results);
    await testEventsAsBytes(results);
    await testLatestEvent(results);
    await testGetEvent(results);
    await testCreator(results);
    await testAncestorRelations(results);
    await testForkDetection(results);
    await testSeesAndStronglySees(results);
    await testRound(results);
    await testWitnesses(results);
  } catch (e) {
    console.error(`\n[ERROR] Test execution failed:`, e);
    return 1;
  }

  return results.summary() ? 0 : 1;
}

main().then((code) => process.exit(code));
