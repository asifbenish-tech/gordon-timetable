// src/world/scripts/index.ts: named scripts (actions "script:<name>") and live room logic.
import type { LogicFactory, ScriptFn } from "../game";
import * as prologue from "./prologue";
import * as act1 from "./act1";
import * as act2 from "./act2";

export const SCRIPTS: Record<string, ScriptFn> = {};
export const LOGIC: Record<string, LogicFactory> = {};

for (const [prefix, mod] of [["prologue", prologue], ["act1", act1], ["act2", act2]] as const) {
  for (const [k, v] of Object.entries(mod.scripts)) SCRIPTS[`${prefix}.${k}`] = v;
  Object.assign(LOGIC, mod.logic);
}
