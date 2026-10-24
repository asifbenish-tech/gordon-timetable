# CHANGELOG

## Release 1 candidate: Episode 1 (Prologue, Act I, Act II)

Everything below runs on placeholder art and placeholder music, so final assets drop in by replacing files.

### M0 Scaffold
- Vite, TypeScript (strict), Phaser 4, Tone.js; ESLint, typecheck, Vitest, content validation; a title
  screen whose Begin button starts audio (`Tone.start()`).

### M1 Clock and voice
- The Conductor (bars and sixteenths on the Transport), the Distaff's voice (clarinet, harp attack,
  glass-harmonica sustain), eight notes by mouse, touch, keys 1-8 and a gamepad radial wheel.
- Latency calibration on first launch, with a Bluetooth warning.

### M2 Drafts
- Seeded draft generator with the melodic rules and fallback pool; matching forwards and backwards;
  the Book of Patterns (Practice writes it, Standard and Expert let you write it; hold to hear).

### M3 Adventure layer
- Rooms from JSON with parallax layers, lights and normal maps; walking with pathfinding; hotspots,
  look and talk, dialogue with portraits and two-note speaker signatures; flags; saves in localStorage
  with export and import; the HTML text layer; the asset manifest; placeholder and normal-map generators.

### M4 Prologue
- P1-P6: the Crossing, the landing, Skein, the crack, the park gate, Marcus, the commuter.
- Skein's three-tier hints.

### M5 Combing
- Stems, the Loom View (pull, isolate, cast on a thread), knots, seals, tethers driven by hit data,
  the golden thread.

### M6 Act I
- A1-1 to A1-7: the receptionist, the mixing desk, the coach's warm-up, the mirrored corridor,
  "The Hit That Ate a Song", Unmasking LYRIX, the talent elevator. The f returns.

### M7 Spindle and Act II
- Spools (two, then four), recording, per-bar re-casts, copying and dropping threads.
- A2-1 to A2-10: Juno, the Beat Press, the conveyor, the mute pedal, the Panel, "The Sidechain Gate",
  the run-of-show, grandmother's piano, Marcus's groove, "The Unplugged Encore". The g returns.

### Release 1 polish
- Captions for music cues, glyphs and colours for every note, contour lines, high contrast, text size,
  hotspot reveal (hold H), keyboard and gamepad play throughout, a phone layout, an installable offline
  build (web manifest and service worker), both name sets building.
- Tests: 100,000-seed draft fuzz, Spindle quantization, golden level, weave recipes, pathfinding,
  content schemas; the Playwright solvability bot over 50 seeds; wrong-move and save tests; the
  one-bar timing test.

### Found by the bot and fixed before release
- A cutscene could wait forever when a busy frame made Tone's Draw drop a bar callback (Draw expiration).
- Live notes and Spindle loops shared one monophonic voice and could collide; loops have their own voice
  and every instrument keeps its start times in order.
- Pulling the knotted vocal uncovered the golden thread without Tuning; it is now braided into the vocal.
- Begin did nothing on a fresh visit (the title music read a save that did not exist yet).
- The lobby desk now stands in front of the receptionist.
