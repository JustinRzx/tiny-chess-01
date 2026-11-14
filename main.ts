// makefun-coin-launch-01 entry: MakeFun Ghost (GHOST).
// Copies LAUNCH.json from the repository root (BOT_DIR) to OUTPUT_DIR/LAUNCH.json.
// The copy is written to a temporary file in OUTPUT_DIR, verified byte-for-byte against the source,
// then renamed into place, so the destination is either absent or complete.
// Node 22+, standard library only. No network access.
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const SRC = join(BOT_DIR, 'LAUNCH.json');
const DEST = join(OUTPUT_DIR, 'LAUNCH.json');
const TMP = join(OUTPUT_DIR, '.LAUNCH.json.tmp');

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}

let data: Buffer;
try {
  data = readFileSync(SRC);
} catch (err) {
  fail(`LAUNCH.json could not be read from ${BOT_DIR}: ${(err as Error).message}`);
}

try {
  mkdirSync(OUTPUT_DIR, { recursive: true });
  writeFileSync(TMP, data);
  const check = readFileSync(TMP);
  if (check.length !== data.length || !check.equals(data)) {
    rmSync(TMP, { force: true });
    fail(`LAUNCH.json copy verification failed: bytes differ after writing ${TMP}`);
  }
  renameSync(TMP, DEST);
} catch (err) {
  rmSync(TMP, { force: true });
  fail(`LAUNCH.json could not be written to ${OUTPUT_DIR}: ${(err as Error).message}`);
}
