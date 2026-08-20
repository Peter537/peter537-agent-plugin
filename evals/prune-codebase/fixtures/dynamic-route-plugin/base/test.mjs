import assert from "node:assert/strict";

import { load } from "./router.mjs";


assert.equal((await load("health"))(), "ok");
assert.equal((await load("import"))(), "imported");
