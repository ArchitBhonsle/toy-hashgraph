mod utils;

use js_sys::{Array, Map, Uint8Array};
use wasm_bindgen::prelude::*;

/// A Hashgraph instance representing a single peer's view of the distributed ledger.
///
/// The Hashgraph data structure is used for Byzantine fault-tolerant consensus.
/// Each peer maintains their own Hashgraph instance and synchronizes with other
/// peers by exchanging events.
#[wasm_bindgen]
pub struct Hashgraph {
    inner: toy_hashgraph::Hashgraph,
}

#[wasm_bindgen]
impl Hashgraph {
    /// Create a new Hashgraph instance for a peer.
    ///
    /// @param id - The unique identifier for this peer.
    /// @param timestamp - The initial timestamp (typically in milliseconds).
    /// @param private_key - The Ed25519 private key for this peer (32 bytes).
    /// @param public_keys - A Map mapping peer IDs (as BigInt) to their Ed25519 public keys (Uint8Array).
    #[wasm_bindgen(constructor)]
    pub fn new(
        id: u64,
        timestamp: u64,
        private_key: &[u8],
        public_keys: &Map,
    ) -> Result<Hashgraph, JsError> {
        if private_key.len() != 32 {
            return Err(JsError::new(
                "private_key should be a Uint8Array of length 32",
            ));
        }

        let mut private_key_bound = [0u8; 32];
        private_key_bound.copy_from_slice(private_key);

        let mut public_keys_vec = Vec::new();

        public_keys.for_each(&mut |value, key| {
            let key_id = key
                .as_f64()
                .map(|f| f as u64)
                .expect("public_keys should be a Map with numeric keys");

            let value = value
                .dyn_into::<Uint8Array>()
                .expect("public_keys should be a Map with Uint8Arrays as values");

            if value.length() != 32 {
                panic!("public_keys should be a Map with Uint8Arrays of length 32 as values");
            }

            let mut buffer = [0u8; 32];
            value.copy_to(&mut buffer);

            public_keys_vec.push((key_id, buffer));
        });

        Ok(Hashgraph {
            inner: toy_hashgraph::Hashgraph::new(id, timestamp, private_key_bound, public_keys_vec),
        })
    }

    /// The unique identifier of this peer.
    #[wasm_bindgen(getter)]
    pub fn id(&self) -> u64 {
        self.inner.id
    }

    /// The pending transactions that will be included in the next event.
    ///
    /// Transactions are accumulated via `appendTransaction()` and are
    /// cleared when a new event is created during `receive()`.
    #[wasm_bindgen(getter, js_name = pendingTransactions)]
    pub fn pending_transactions(&self) -> Uint8Array {
        Uint8Array::from(self.inner.pending_transactions.as_slice())
    }

    /// The Ed25519 private key used for signing events (32 bytes).
    #[wasm_bindgen(getter)]
    pub fn signer(&self) -> Uint8Array {
        Uint8Array::from(self.inner.signer.to_bytes().as_slice())
    }

    /// A Map mapping peer IDs (BigInt) to their Ed25519 public keys (Uint8Array, 32 bytes each).
    #[wasm_bindgen(getter)]
    pub fn verifiers(&self) -> Map {
        let map = Map::new();
        for (id, key) in &self.inner.verifiers {
            let key_bytes = Uint8Array::from(key.to_bytes().as_slice());
            map.set(&JsValue::from(*id), &key_bytes);
        }
        map
    }

    /// Get a read-only querier for the underlying graph structure.
    ///
    /// The GraphQuerier provides methods to inspect the graph, check
    /// ancestry relationships, compute rounds, and more.
    ///
    /// Note: This returns a clone of the graph at the current point in time.
    /// Changes to the Hashgraph after calling this will not be reflected
    /// in the returned GraphQuerier.
    #[wasm_bindgen(getter)]
    pub fn graph(&self) -> GraphQuerier {
        GraphQuerier {
            inner: self.inner.graph.clone(),
        }
    }

    /// Append transaction data to the pending transactions buffer.
    ///
    /// The accumulated transactions will be included in the next event
    /// created during a `receive()` call.
    #[wasm_bindgen(js_name = appendTransaction)]
    pub fn append_transaction(&mut self, transaction: &[u8]) {
        self.inner.append_transaction(transaction);
    }

    /// Prepare a message to send to another peer.
    ///
    /// This serializes the current graph state along with a signature
    /// for verification by the receiving peer.
    ///
    /// @returns A Uint8Array containing the signed message to send.
    pub fn send(&mut self) -> Uint8Array {
        Uint8Array::from(self.inner.send().as_slice())
    }

    /// Receive and process a message from another peer.
    ///
    /// This updates the local graph with events from the sender and
    /// creates a new event referencing both the local latest event
    /// and the sender's latest event. Pending transactions are included.
    ///
    /// @param data - The signed message from another peer (from their `send()`).
    /// @param timestamp - The current timestamp for the new event.
    pub fn receive(&mut self, data: &[u8], timestamp: u64) {
        self.inner.receive(data, timestamp);
    }

    /// Serialize the entire Hashgraph state to JSON.
    ///
    /// @returns A JSON string containing the id, pending transactions, and graph.
    #[wasm_bindgen(js_name = asJson)]
    pub fn as_json(&self) -> String {
        self.inner.as_json()
    }

    /// Create a deep copy of this Hashgraph.
    ///
    /// @returns A new Hashgraph instance with the same state.
    #[wasm_bindgen(js_name = clone)]
    pub fn clone_hashgraph(&self) -> Hashgraph {
        Hashgraph {
            inner: self.inner.clone(),
        }
    }
}

/// An interface for querying the graph structure of a Hashgraph.
///
/// This class provides methods to inspect events, check ancestry relationships,
/// compute consensus rounds, and identify witnesses. Methods that perform
/// computations will cache their results for improved performance.
///
/// Obtain a GraphQuerier via the `Hashgraph.graph` property, or construct one
/// from JSON using `GraphQuerier.fromJson()`.
#[wasm_bindgen]
pub struct GraphQuerier {
    inner: toy_hashgraph::graph::Graph,
}

#[wasm_bindgen]
impl GraphQuerier {
    /// Create a GraphQuerier from a JSON string.
    ///
    /// @param json - A JSON string representing the graph (as produced by `asJson()`).
    /// @returns A new GraphQuerier instance.
    #[wasm_bindgen(js_name = fromJson)]
    pub fn from_json(json: &str) -> GraphQuerier {
        GraphQuerier {
            inner: toy_hashgraph::graph::Graph::from_json(json),
        }
    }

    /// Serialize the graph to JSON.
    ///
    /// @returns A JSON object with the following structure:
    ///   - `total_peers`: The total number of peers in the network.
    ///   - `events`: An object mapping event hashes (hex) to event data.
    #[wasm_bindgen(js_name = asJson)]
    pub fn as_json(&self) -> String {
        self.inner.as_json()
    }

    /// The total number of peers in the network.
    #[wasm_bindgen(getter, js_name = totalPeers)]
    pub fn total_peers(&self) -> usize {
        self.inner.total_peers
    }

    /// Check if a count represents a supermajority of peers.
    ///
    /// A supermajority is more than 2/3 of the total peers.
    ///
    /// @param count - The number to check.
    /// @returns True if count > (2/3 * total_peers).
    #[wasm_bindgen(js_name = isSupermajority)]
    pub fn is_supermajority(&self, count: usize) -> bool {
        self.inner.is_supermajority(count)
    }

    /// Serialize all events in the graph to bytes.
    #[wasm_bindgen(js_name = eventsAsBytes)]
    pub fn events_as_bytes(&self) -> Uint8Array {
        Uint8Array::from(self.inner.events_as_bytes().as_slice())
    }

    /// Get the hash of the latest event created by a specific peer.
    ///
    /// The latest event is the one with no descendants in the peer's chain.
    ///
    /// @param peer - The peer ID to query.
    /// @returns The event hash (Uint8Array, 32 bytes), or null if no events exist for this peer.
    #[wasm_bindgen(js_name = latestEvent)]
    pub fn latest_event(&mut self, peer: u64) -> Option<Uint8Array> {
        self.inner
            .latest_event(peer)
            .map(|hash| Uint8Array::from(hash.as_slice()))
    }

    /// Get an event by its hash.
    ///
    /// @param eventHash - The SHA-256 hash of the event (Uint8Array 32 bytes or hex string).
    /// @returns The event as a JSON string.
    #[wasm_bindgen(js_name = getEvent)]
    pub fn get_event(&self, event_hash: &JsValue) -> Result<String, JsError> {
        let hash = extract_hash(event_hash)?;
        let event = self.inner.get_event(&hash);
        serde_json::to_string(event)
            .map_err(|e| JsError::new(&format!("failed to serialize event: {}", e)))
    }

    /// Get the peer ID of the creator of an event.
    ///
    /// This follows the self-parent chain back to the initial event.
    ///
    /// @param eventHash - The SHA-256 hash of the event (Uint8Array 32 bytes or hex string).
    /// @returns The peer ID of the event's creator.
    pub fn creator(&mut self, event_hash: &JsValue) -> Result<u64, JsError> {
        let hash = extract_hash(event_hash)?;
        Ok(self.inner.creator(&hash))
    }

    /// Check if event x is an ancestor of event y (x ≤ y).
    ///
    /// An event is an ancestor of another if there is a path through
    /// parent references. Every event is an ancestor of itself.
    ///
    /// @param x - Hash of the potential ancestor event (Uint8Array 32 bytes or hex string).
    /// @param y - Hash of the potential descendant event (Uint8Array 32 bytes or hex string).
    /// @returns True if x is an ancestor of y (including x == y).
    #[wasm_bindgen(js_name = isAncestor)]
    pub fn is_ancestor(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.is_ancestor(&x_hash, &y_hash))
    }

    /// Check if event x is a strict ancestor of event y (x < y).
    ///
    /// Same as isAncestor but excludes the case where x == y.
    #[wasm_bindgen(js_name = isStrictAncestor)]
    pub fn is_strict_ancestor(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.is_strict_ancestor(&x_hash, &y_hash))
    }

    /// Check if event x is a self-ancestor of event y (x ⊑ y).
    ///
    /// A self-ancestor relationship follows only the self-parent chain,
    /// meaning both events were created by the same peer.
    #[wasm_bindgen(js_name = isSelfAncestor)]
    pub fn is_self_ancestor(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.is_self_ancestor(&x_hash, &y_hash))
    }

    /// Check if event x is a strict self-ancestor of event y (x ⊏ y).
    ///
    /// Same as isSelfAncestor but excludes the case where x == y.
    #[wasm_bindgen(js_name = isStrictSelfAncestor)]
    pub fn is_strict_self_ancestor(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.is_strict_self_ancestor(&x_hash, &y_hash))
    }

    /// Check if two events represent a fork (Byzantine behavior).
    ///
    /// A fork occurs when two events from the same creator are not
    /// in a self-ancestor relationship with each other.
    #[wasm_bindgen(js_name = isFork)]
    pub fn is_fork(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.is_fork(&x_hash, &y_hash))
    }

    /// Check if an event can see evidence of dishonesty by a peer.
    ///
    /// An event can see dishonesty if it has visibility to a fork
    /// created by the specified peer.
    #[wasm_bindgen(js_name = canSeeDishonesty)]
    pub fn can_see_dishonesty(&mut self, event_hash: &JsValue, peer: u64) -> Result<bool, JsError> {
        let hash = extract_hash(event_hash)?;
        Ok(self.inner.can_see_dishonesty(&hash, peer))
    }

    /// Check if event y sees event x (x ⊴ y).
    ///
    /// Event y sees event x if x is an ancestor of y and y cannot
    /// see any dishonesty by the creator of x.
    pub fn sees(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.sees(&x_hash, &y_hash))
    }

    /// Check if event y strongly sees event x (x ≪ y).
    ///
    /// Event y strongly sees event x if there is a supermajority of
    /// peers whose events are ancestors of y and see x.
    #[wasm_bindgen(js_name = stronglySees)]
    pub fn strongly_sees(&mut self, x: &JsValue, y: &JsValue) -> Result<bool, JsError> {
        let x_hash = extract_hash(x)?;
        let y_hash = extract_hash(y)?;
        Ok(self.inner.strongly_sees(&x_hash, &y_hash))
    }

    /// Compute the round number of an event.
    ///
    /// Initial events are in round 0. Other events advance to round r+1
    /// if they can strongly see a supermajority of round r witnesses.
    pub fn round(&mut self, event_hash: &JsValue) -> Result<u64, JsError> {
        let hash = extract_hash(event_hash)?;
        Ok(self.inner.round(&hash))
    }

    /// Get all witness events for a specific round.
    ///
    /// A witness is the first event by a peer in a given round.
    /// Initial events are witnesses for round 0.
    ///
    /// @returns An array of event hashes (Uint8Array, 32 bytes each).
    pub fn witnesses(&mut self, round: u64) -> Array {
        let witnesses = self.inner.witnesses(round);
        let arr = Array::new();
        for hash in witnesses {
            arr.push(&Uint8Array::from(hash.as_slice()));
        }
        arr
    }

    /// Get all famous witness events for a specific round.
    ///
    /// A famous witness is a witness that has been decided as famous
    /// through the voting process.
    ///
    /// @returns An array of event hashes (Uint8Array, 32 bytes each).
    #[wasm_bindgen(js_name = famousWitnesses)]
    pub fn famous_witnesses(&mut self, round: u64) -> Array {
        let witnesses = self.inner.famous_witnesses(round);
        let arr = Array::new();
        for hash in witnesses {
            arr.push(&Uint8Array::from(hash.as_slice()));
        }
        arr
    }

    /// Get the unique famous witnesses for a specific round.
    ///
    /// When a peer has multiple famous witnesses (due to forks),
    /// only the minimum hash is kept per peer.
    ///
    /// @returns An array of event hashes (Uint8Array, 32 bytes each).
    #[wasm_bindgen(js_name = uniqueFamousWitnesses)]
    pub fn unique_famous_witnesses(&mut self, round: u64) -> Array {
        let witnesses = self.inner.unique_famous_witnesses(round);
        let arr = Array::new();
        for hash in witnesses {
            arr.push(&Uint8Array::from(hash.as_slice()));
        }
        arr
    }

    /// Get the round in which an event was received (achieved consensus).
    ///
    /// An event is received in round r if all unique famous witnesses
    /// of round r are descendants of the event.
    ///
    /// @returns The round number, or null if consensus has not been reached.
    #[wasm_bindgen(js_name = roundReceived)]
    pub fn round_received(&mut self, event_hash: &JsValue) -> Result<Option<u64>, JsError> {
        let hash = extract_hash(event_hash)?;
        Ok(self.inner.round_received(&hash))
    }

    /// Get the consensus timestamp for an event.
    ///
    /// The consensus timestamp is the median of the timestamps when
    /// each unique famous witness first saw the event.
    ///
    /// @returns The consensus timestamp, or null if consensus has not been reached.
    #[wasm_bindgen(js_name = consensusTimestamp)]
    pub fn consensus_timestamp(&mut self, event_hash: &JsValue) -> Result<Option<u64>, JsError> {
        let hash = extract_hash(event_hash)?;
        Ok(self.inner.consensus_timestamp(&hash))
    }

    /// Compare two events by their consensus ordering.
    ///
    /// Events are ordered by: round received, then consensus timestamp,
    /// then by their hash as a tiebreaker.
    ///
    /// @returns -1 if a < b, 0 if a == b, 1 if a > b, or null if either
    ///          event has not yet reached consensus.
    #[wasm_bindgen(js_name = consensusOrdering)]
    pub fn consensus_ordering(&mut self, a: &JsValue, b: &JsValue) -> Result<Option<i8>, JsError> {
        let a_hash = extract_hash(a)?;
        let b_hash = extract_hash(b)?;
        Ok(self
            .inner
            .consensus_ordering(a_hash, b_hash)
            .map(|ordering| match ordering {
                std::cmp::Ordering::Less => -1,
                std::cmp::Ordering::Equal => 0,
                std::cmp::Ordering::Greater => 1,
            }))
    }
}

fn extract_hash(value: &JsValue) -> Result<[u8; 32], JsError> {
    // Try Uint8Array first
    if let Ok(arr) = value.clone().dyn_into::<Uint8Array>() {
        if arr.length() != 32 {
            return Err(JsError::new("hash should be a Uint8Array of length 32"));
        }
        let mut hash = [0u8; 32];
        arr.copy_to(&mut hash);
        return Ok(hash);
    }

    // Try string (hex)
    if let Some(hex_str) = value.as_string() {
        // Strip optional "0x" prefix
        let hex_str = hex_str.strip_prefix("0x").unwrap_or(&hex_str);

        if hex_str.len() != 64 {
            return Err(JsError::new(
                "hash hex string should be 64 characters (32 bytes)",
            ));
        }

        let mut hash = [0u8; 32];
        for (i, chunk) in hex_str.as_bytes().chunks(2).enumerate() {
            let hex_byte =
                std::str::from_utf8(chunk).map_err(|_| JsError::new("invalid hex string"))?;
            hash[i] =
                u8::from_str_radix(hex_byte, 16).map_err(|_| JsError::new("invalid hex string"))?;
        }
        return Ok(hash);
    }

    Err(JsError::new(
        "hash should be a Uint8Array (32 bytes) or a hex string (64 characters)",
    ))
}

#[wasm_bindgen(start)]
fn run() {
    utils::set_panic_hook();
}
