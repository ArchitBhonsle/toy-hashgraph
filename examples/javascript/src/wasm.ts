/**
 * WASM loader for Bun runtime.
 *
 * The bundler target from wasm-pack uses ESM wasm imports which don't work
 * directly in Bun. This module manually loads the wasm and initializes it.
 */

import { fileURLToPath } from "url";
import { dirname, join } from "path";

// Path to the wasm file
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const wasmPath = join(
  __dirname,
  "../../../toy-hashgraph-js/pkg/toy_hashgraph_js_bg.wasm"
);
const bgJsPath = join(
  __dirname,
  "../../../toy-hashgraph-js/pkg/toy_hashgraph_js_bg.js"
);

// Re-export types with different names to avoid conflict
import type {
  Hashgraph as HashgraphType,
  GraphQuerier as GraphQuerierType,
} from "../../../toy-hashgraph-js/pkg/toy_hashgraph_js.d.ts";

export type Hashgraph = HashgraphType;
export type GraphQuerier = GraphQuerierType;

// The background JS module type
interface BgModule {
  __wbg_set_wasm: (wasm: WebAssembly.Exports) => void;
  Hashgraph: new (
    id: bigint,
    timestamp: bigint,
    private_key: Uint8Array,
    public_keys: Map<unknown, unknown>
  ) => HashgraphType;
  GraphQuerier: {
    fromJson(json: string): GraphQuerierType;
  };
  [key: string]: unknown;
}

// Build the import object that the wasm module expects
function getImportObject(bg: BgModule): WebAssembly.Imports {
  const imports: Record<string, WebAssembly.ImportValue> = {};

  for (const [key, value] of Object.entries(bg)) {
    if (key.startsWith("__wbg_") || key.startsWith("__wbindgen_")) {
      imports[key] = value as WebAssembly.ImportValue;
    }
  }

  return { "./toy_hashgraph_js_bg.js": imports };
}

let initialized = false;
let bgModule: BgModule;

/**
 * Initialize the WASM module. Must be called before using any exports.
 * Safe to call multiple times - will only initialize once.
 */
export async function init(): Promise<void> {
  if (initialized) return;

  // Dynamic import the background JS
  bgModule = (await import(bgJsPath)) as BgModule;

  const wasmBuffer = await Bun.file(wasmPath).arrayBuffer();
  const importObject = getImportObject(bgModule);

  const { instance } = await WebAssembly.instantiate(wasmBuffer, importObject);

  // Set the wasm module in the bindings
  bgModule.__wbg_set_wasm(instance.exports);

  // Initialize the externref table if the function exists
  const exports = instance.exports as { __wbindgen_start?: () => void };
  if (typeof exports.__wbindgen_start === "function") {
    exports.__wbindgen_start();
  }

  initialized = true;
}

function ensureInitialized(): void {
  if (!initialized) {
    throw new Error("WASM not initialized. Call init() first.");
  }
}

/**
 * Create a new Hashgraph instance.
 * Requires init() to be called first.
 */
export function createHashgraph(
  id: bigint,
  timestamp: bigint,
  privateKey: Uint8Array,
  publicKeys: Map<number, Uint8Array>
): Hashgraph {
  ensureInitialized();
  return new bgModule.Hashgraph(id, timestamp, privateKey, publicKeys);
}

/**
 * Create a GraphQuerier from JSON.
 * Requires init() to be called first.
 */
export function createGraphQuerierFromJson(json: string): GraphQuerier {
  ensureInitialized();
  return bgModule.GraphQuerier.fromJson(json);
}

// For direct class access (advanced usage)
export function getHashgraphClass(): BgModule["Hashgraph"] {
  ensureInitialized();
  return bgModule.Hashgraph;
}

export function getGraphQuerierClass(): BgModule["GraphQuerier"] {
  ensureInitialized();
  return bgModule.GraphQuerier;
}
