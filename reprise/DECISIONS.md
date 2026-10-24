# DECISIONS.md

Every judgment call the design document leaves open, with the section it interprets. Conflicts between
sections are marked **Conflict** and were resolved by the document's own order: section 10 over 9 over 6
over 4 over everything else, and, when that still left a dead end, "the simplest behaviour that keeps the
no-dead-ends rule" (section 10).

## Scope and process

**D-001 · Release 1 only (§0, §10).** This build covers the Prologue, Act I and Act II (M0 to M7 and the
Release 1 polish). Act III, Act IV and the finale are Release 2 and are not started: "Finish and ship
Release 1 before starting Act III." The owner asked for the game to be built in one go, so milestones M0 to
M7 were built back to back rather than reviewed one by one; the review now happens on Release 1 as a whole.

**D-002 · Where the code lives.** The only repository attached to this session is the school timetable
(`gordon-timetable`), whose `master` branch is published to teachers. The game sits in a self-contained
`reprise/` folder on a work branch, touches nothing else, and is never merged into `master` by this work.
It should move to its own repository before it is published on GitHub Pages or itch.io.

**D-003 · Default name set: `original` (§1).** The owner picks the set at build time. `npm run build`
uses `original` (Tam Threadwell, the Weavers, *Reprise*) because it is the takedown-safe set;
`npm run build:loom` builds with `loom`. Nothing else differs. A content check fails the build if a
franchise name is written into `strings/en.json` instead of coming from `names.json`.

## Drafts and notes

**D-004 · Draft generator retries (§9.6).** With five reversible drafts on only c, d and e, the greedy
generator of §9.6 paints itself into a corner for about 2% of seeds (no room left for Unmasking, even in
the fallback pool). `generateDrafts` runs §9.6's loop again from the same random stream, up to 20 times.
The result is still a pure function of the seed. The unit test checks every rule over 100,000 seeds.

**D-005 · Conflict: Unmasking's note range (§6 puzzle 1 vs §4.2 and the puzzle map).** Puzzle 1 says the
four notes are "randomized from c-f". But §4.2 says a draft only uses notes Bobbin owns when it is taught,
f only returns at A1-6, and A1-6 is cast *with* Unmasking: an f in Unmasking would make A1-6 unplayable,
a dead end. Unmasking, like Tuning, uses c-e (`highestNote: 2`). Act II drafts use c-f, Act III c-g,
Act IV c-a.

**D-006 · Conflict: "two puzzles open at once" (§6.4).** The rule says that after each act's first two
puzzles at least two puzzles must be open, climaxes excepted. The fixed needs in the same table make A1-5
to A1-7 and A2-6 to A2-7 strictly sequential. The table's needs are "implement exactly" (§0), so they win;
the rule holds where the table allows it (A1-3 with A1-4, A2-3 with A2-4, A2-8 with A2-9).

**D-007 · The two-beat reset (§9.6) and pillar 6.** A half-played draft resets after two beats of silence,
as in §9.6's code. Because a fast tempo makes two beats short, Settings also offers "four beats" and
"never". The default is the document's.

**D-008 · The Distaff before the crack (§3, §4.6).** During the Crossing the Distaff is whole (eight notes);
the crack in P3 leaves c, d and e. The flock's calls only use c-e, so nothing learned there is lost.

## Combing, the Spindle and puzzles

**D-009 · How long a pull lasts (§4.3).** "While the Loom View is open, or until put back": closing the
Loom View puts every pulled thread back. Knots untied by Tuning stay untied (a change).

**D-010 · Solved routes stay open.** No dead ends (§0): once a route is opened by a state, it stays open.
The A1-4 dancers, frozen without their click, drift off to find a beat; Juno wedges the Sidechain Gate;
the conveyor ride is remembered. Every teaching source and every thread source stays where it is.

**D-011 · Learning by isolating (A1-3).** The coach's scale is learned the moment her voice thread is
isolated, and she sings it once clearly. Isolation is a hold, so learning on release would be a timing test.

**D-029 · The golden thread is braided (§6 puzzle 1, §9.6).** The golden thread "is braided with" the
knotted lead vocal, so pulling or hushing the vocal while the knot is tied takes the golden thread with it
(`braid` on the golden stem). Without this, pulling every thread uncovered it and skipped Tuning, which the
solvability bot's wrong-move test caught. §9.6's masking formula is unchanged.

**D-012 · Puzzle 2's alarm (§6).** One Hushing on the kick: the gate opens for exactly that bar, and the
DEAD AIR klaxon sounds as the silent bar ends; the scene resets. Hushing looped before the kick is covered:
the alarm sounds after two bars and the foreman clears the spool that holds the loop. Walking through
needs the copy on a spool *and* the loop.

**D-013 · Puzzle 3's counter-moves (§6).** Dominic reacts to states, not to an order of clicks: both drops
done -> the canned chant appears; the chant held silent by a loop and the microphone open -> he knots
Lyra's live voice; Tuning on it -> the encore. Rousing on the muted microphone works for one bar; looped,
it opens the microphone, but her recorded voice still plays over her, so the crowd hears two Lyras.

**D-014 · A2-8's out-of-tune copy.** Copying the piano before Tuning gives "the piano (out of tune)",
which Lyra will not turn for. A2-8 is solved by a copy of the tuned piano.

**D-015 · "Solved when" for learning and carrying.** Learning a draft sets `learned_<id>`; copying a
thread sets `spooled:<song>:<stem>`. A puzzle never counts as solved before its needs are met, even if
its flag was set early.

**D-016 · Hints before Skein (§4.7).** Skein becomes the hint system in P2 (she is the one fading in P2).
P1 and P2 have hint text in their files, but nobody gives it yet; both are short and teach themselves.

## Sound and music

**D-017 · Placeholder music pipeline (§8.9).** Hand-writing binary MIDI is not practical, so each song's
editable source is notation JSON in `music/src/`. `tools/render-stems.py` writes the `.mid` file for
musicians, the hit data the game reads, and the expanded notes the placeholder synths play. With FluidSynth
and a `$SOUNDFONT` installed it also renders OGG and M4A stems, normalised with ffmpeg to -18 LUFS / -1 dBTP
(§8.7), and marks them `generated`. Without them, stems stay `placeholder` and play in the browser from the
same notes, so swapping in real stems changes no code.

**D-018 · The score's sources (§8.1, §8.6).** No recording of any piece is used. The swan theme (Tchaikovsky)
and the Neptune-like choir (Holst) are short approximations written from memory, marked placeholder. The
Rhapsody in Blue arrangements need transcription from Gershwin's 1924 two-piano score, which this build
cannot verify note for note; every Rhapsody cue (title, factory, Lyra's andantino) is original placeholder
material in a similar idiom until a musician arranges from the public-domain score. Lyra's song and the
hooks are newly written (§8.1).

**D-019 · The Distaff bed (§8.4).** Simplified: the score ducks while Bobbin plays and comes back after a
cast. The vamp re-arrangement around C is left for when real stems exist.

**D-020 · Expert's golden thread (§6 build notes).** In Expert the golden thread's volume is its level
cubed, so it stays quieter for longer. Expert's extra closing scene belongs to the finale (Release 2).

## Look

**D-021 · Drained and restored (§7.3, §7.4).** Placeholder rooms are drawn once in the location's colours.
"Drained" is a camera colour-matrix that desaturates them; restoring a location (f for the park and the
Spire, g for the factory and the arena) lifts it. Drained rooms animate locked to the beat; restored rooms
drift. The flock's whiteness grows with each note won back after the crack.

**D-022 · Lighting (§7.2).** Characters and one background layer per room are lit with normal maps from
`tools/make-normals.ts`. The banded light post-filter is not used; the placeholders bake dithered bands in.
Settings has a low-detail switch that turns lighting off.

**D-023 · Below 1x (§7.1).** On a screen smaller than 640x360 (a phone held upright) there is no whole-number
scale, so the stage shrinks fractionally and a hint suggests turning the phone. At 1x and above, scaling is
whole numbers only.

**D-024 · Close-up icons (§4.1).** The selected object's icon is the first frame of its sprite, drawn
pixel for pixel; objects painted into the background show their initial.

## Data formats (§9.5) extensions

**D-025 · Extra fields.** `HotspotDef` gains `name`, `talk`, `listen`, `person`, `stand`, `when`, `sprite`
and `exit`; `StemDef` gains `label`, `instrument`, `when` and `level`; `PuzzleDef` gains `room`, `focus`
and `title`; dialogue nodes gain `else`. Draft actions on the room itself live on a `_self` hotspot.
Actions may be chained with `;`. Scripts receive whether a cast came from a loop, so looped casts stay
quiet. All marked "ext" in `src/content/types.ts`.

**D-026 · Rooms and strings were first written by generator scripts.** The JSON under `content/` is now
the source of truth and is edited directly.

## Testing

**D-027 · The bot's speed (§9.8).** The solvability bot plays through the real AudioContext at four times
the tempo, with lines that don't wait to be read, one page at a time. Running several headless pages at
once on a small machine starves them of audio time and makes bar-based states flaky.

**D-028 · The timing test (§9.8).** An offline render of one bar with two spools, using one-sample impulses
on raw buffer sources so the first non-zero sample is exactly where each note landed. Synth onsets were
tried first and measured the synth's attack, not the scheduler.
