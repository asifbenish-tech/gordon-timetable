#!/usr/bin/env python3
"""tools/render-stems.py: music/src notation -> MIDI, hit data and stems (GDD 8.9).

For every music/src/<song>.json this script:
  1. expands the notation into note events per track,
  2. writes music/src/<song>.mid (one MIDI track per stem) for musicians,
  3. writes assets/audio/stems/<song>/<stem>.notes.json (the placeholder synth plays it)
     and <stem>.hits.json (note-on beats; gameplay reads these, never audio),
  4. if FluidSynth and a General MIDI soundfont ($SOUNDFONT) are installed, renders each
     stem to OGG and M4A, loudness-normalised with ffmpeg to -18 LUFS / -1 dBTP,
     and marks the stem "generated" in assets/manifest.json. Otherwise stems stay
     "placeholder" and the browser synthesises them.

Notation (DECISIONS.md D-017):
  "steps": "x...x...|x.x.x..." one char per 16th, bars split by |, X accent, x normal, o soft
  "notes": "c4:1 e4:.5 [c4,e4,g4]:2 r:1 | ..."  pitch:beats, r = rest, ! accent, ? soft
  "@0:1"  = note 0 of this save's draft named in "draft" (per-save melodies, GDD 8.9 step 6)
  Patterns repeat to fill the song's bars. "swing" (0..0.5) delays every off-beat eighth by that share of an eighth.
"""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "music", "src")
STEMS = os.path.join(ROOT, "assets", "audio", "stems")
MANIFEST = os.path.join(ROOT, "assets", "manifest.json")

NAMES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
GM_PROGRAM = {"piano": 0, "piano_old": 0, "bass": 38, "saw": 81, "vocal": 54, "pad": 89, "strings": 48,
              "clarinet": 71, "harp": 46, "choir": 52, "coach": 53, "hum": 53, "arp": 80, "jingle": 14,
              "chant": 52, "swan": 68, "hum_machine": 87, "press": 12, "pedal": 115}
DRUMS = {"kick": 36, "clap": 39, "hat": 42, "snare": 38, "bucket": 45, "click": 37, "riser": 49, "crowd": 46}


def pitch(tok):
    m = re.fullmatch(r"([a-g])([#b]?)(-?\d)", tok)
    if not m:
        raise ValueError(f"bad pitch {tok}")
    n = NAMES[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + n


def dur(s):
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def parse_notes(text):
    """Returns events [t, pitch_or_ref, d, v] for one pass of the pattern and its length in beats."""
    events, t = [], 0.0
    for bar in text.split("|"):
        for tok in bar.split():
            v = 0.8
            if tok.endswith("!"):
                v, tok = 1.0, tok[:-1]
            elif tok.endswith("?"):
                v, tok = 0.5, tok[:-1]
            head, _, d = tok.rpartition(":")
            d = dur(d)
            if head != "r":
                if head.startswith("["):
                    for p in head[1:-1].split(","):
                        events.append([t, pitch(p), d, v])
                elif head.startswith("@"):
                    idx, _, octv = head[1:].partition("^")
                    events.append([t, {"k": int(idx), "o": int(octv or 0)}, d, v])
                else:
                    events.append([t, pitch(head), d, v])
            t += d
    return events, t


def parse_steps(text, p):
    events, t = [], 0.0
    for bar in text.split("|"):
        bar = bar.strip()
        if len(bar) != 16:
            raise ValueError(f"step bar must be 16 chars: {bar!r}")
        for ch in bar:
            if ch in "Xxo":
                events.append([t, p, 0.25, {"X": 1.0, "x": 0.8, "o": 0.45}[ch]])
            t += 0.25
    return events, t


def expand(track, bars):
    total = bars * 4.0
    if "steps" in track:
        one, length = parse_steps(track["steps"], pitch(track.get("pitch", "c2")))
    else:
        one, length = parse_notes(track["notes"])
    if length <= 0 or abs(total / length - round(total / length)) > 1e-6:
        raise ValueError(f"pattern of {length} beats does not divide {total}")
    out = []
    for rep in range(int(round(total / length))):
        for t, p, d, v in one:
            out.append([t + rep * length, p, d, v])
    swing = track.get("swing", 0)
    for e in out:
        pos = e[0] * 2
        if swing and abs(pos - round(pos)) < 1e-6 and int(round(pos)) % 2 == 1:
            e[0] += swing * 0.5
    return out


def to_json_events(events):
    res = []
    for t, p, d, v in events:
        ev = {"t": round(t, 4), "d": round(d, 4), "v": v}
        if isinstance(p, dict):
            ev.update(p)
            ev["m"] = -1
        else:
            ev["m"] = p
        res.append(ev)
    return res


def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def midi_file(song, tracks):
    ppq = 480
    chunks = []
    tempo = int(60_000_000 / song["bpm"])
    meta = b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xff\x58\x04\x04\x02\x18\x08" + b"\x00\xff\x2f\x00"
    chunks.append(b"MTrk" + struct.pack(">I", len(meta)) + meta)
    for ch_i, (name, inst, events) in enumerate(tracks):
        drum = inst in DRUMS
        ch = 9 if drum else ch_i % 9
        msgs = []
        for t, p, d, v in events:
            note = DRUMS[inst] if drum else (60 + p["k"] * 2 + 12 * p["o"] if isinstance(p, dict) else p)
            vel = max(1, min(127, int(v * 110)))
            msgs.append((int(t * ppq), 1, bytes([0x90 | ch, note, vel])))
            msgs.append((int((t + d) * ppq), 0, bytes([0x80 | ch, note, 0])))
        msgs.sort(key=lambda m: (m[0], m[1]))
        body = b"\x00\xff\x03" + vlq(len(name)) + name.encode()
        if not drum:
            body += b"\x00" + bytes([0xC0 | ch, GM_PROGRAM.get(inst, 0)])
        last = 0
        for tick, _, msg in msgs:
            body += vlq(tick - last) + msg
            last = tick
        body += b"\x00\xff\x2f\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(body)) + body)
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), ppq)
    return header + b"".join(chunks)


def can_render():
    sf = os.environ.get("SOUNDFONT")
    return bool(shutil.which("fluidsynth") and shutil.which("ffmpeg") and sf and os.path.exists(sf)), sf


def render(song, name, inst, events, out_base, sf):
    with tempfile.TemporaryDirectory() as tmp:
        mid = os.path.join(tmp, "stem.mid")
        with open(mid, "wb") as f:
            f.write(midi_file(song, [(name, inst, events)]))
        wav = os.path.join(tmp, "stem.wav")
        subprocess.run(["fluidsynth", "-ni", "-F", wav, "-r", "48000", sf, mid], check=True, capture_output=True)
        norm = "loudnorm=I=-18:TP=-1:LRA=11"
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-af", norm, "-c:a", "libvorbis", out_base + ".ogg"], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-af", norm, "-c:a", "aac", out_base + ".m4a"], check=True, capture_output=True)


def main():
    ok, sf = can_render()
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"images": [], "audio": []}
    audio = {a["id"]: a for a in manifest.get("audio", [])}
    songs = sorted(f for f in os.listdir(SRC) if f.endswith(".json"))
    for fn in songs:
        song = json.load(open(os.path.join(SRC, fn)))
        sid = song["id"]
        tracks = []
        os.makedirs(os.path.join(STEMS, sid), exist_ok=True)
        for name, tr in song["tracks"].items():
            events = expand(tr, song["bars"])
            tracks.append((name, tr["instrument"], events))
            base = os.path.join(STEMS, sid, name)
            notes = {"bars": song["bars"], "instrument": tr["instrument"], "draft": tr.get("draft"), "notes": to_json_events(events)}
            hits = sorted({round(e[0], 4) for e in events})
            with open(base + ".notes.json", "w") as f:
                json.dump(notes, f, separators=(",", ":"))
            with open(base + ".hits.json", "w") as f:
                json.dump({"hits": hits}, f, separators=(",", ":"))
            rel = f"audio/stems/{sid}/{name}"
            status = audio.get(f"{sid}/{name}", {}).get("status", "placeholder")
            if ok and status != "final" and not tr.get("draft"):
                render(song, name, tr["instrument"], events, base, sf)
                status = "generated"
            audio[f"{sid}/{name}"] = {"id": f"{sid}/{name}", "path": rel, "notes": rel + ".notes.json", "hits": rel + ".hits.json", "status": status}
        with open(os.path.join(SRC, sid + ".mid"), "wb") as f:
            f.write(midi_file(song, tracks))
    manifest["audio"] = [audio[k] for k in sorted(audio)]
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print(f"{len(songs)} songs, {len(audio)} stems" + ("" if ok else " (no FluidSynth/$SOUNDFONT: stems stay placeholder, synthesised in the browser)"))


if __name__ == "__main__":
    sys.exit(main())
