"""Sound generation for the Music deck.

Everything is expressed as a *set of MIDI note numbers sounding together*, so a
single note is just the one-element case of a chord:

    render([60])            # middle C
    render([60, 64, 67])    # C major triad
    render_sequence([[60], [67]])  # melodic fifth: C4 then G4
    write_mp3(render(...), "out.mp3")

Timbre is a simple piano-like additive synth: each note is a stack of partials
with 1/n amplitudes, slight inharmonic stretch, and per-partial exponential
decay (upper partials die faster), under a short attack / release envelope.
Output is deterministic, so rebuilding never produces spurious media drift.
"""

import subprocess

import numpy as np

SAMPLE_RATE = 44100
A4_MIDI = 69
A4_HZ = 440.0

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_hz(midi):
    return A4_HZ * 2 ** ((midi - A4_MIDI) / 12)


def midi_name(midi):
    """60 -> 'C4', 61 -> 'C#4' (scientific pitch notation)."""
    return f"{PITCH_CLASSES[midi % 12]}{midi // 12 - 1}"


def _voice(midi, n_samples, partials=12, inharmonicity=0.0004):
    """One piano-ish note, unnormalized."""
    t = np.arange(n_samples) / SAMPLE_RATE
    f0 = midi_to_hz(midi)
    # Higher notes ring shorter, like real strings.
    base_decay = 1.2 * (f0 / 261.63) ** 0.5
    out = np.zeros(n_samples)
    for n in range(1, partials + 1):
        fn = n * f0 * np.sqrt(1 + inharmonicity * n * n)
        if fn >= SAMPLE_RATE / 2:
            break
        amp = 1.0 / n
        decay = base_decay * (1 + 0.6 * (n - 1))
        out += amp * np.exp(-decay * t) * np.sin(2 * np.pi * fn * t)
    return out


def render(midis, duration=2.0, peak=0.8):
    """Render MIDI notes sounding simultaneously; returns float samples in [-peak, peak]."""
    n = int(duration * SAMPLE_RATE)
    mix = sum(_voice(m, n) for m in midis)
    attack = int(0.005 * SAMPLE_RATE)
    release = int(0.15 * SAMPLE_RATE)
    env = np.ones(n)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release)
    mix *= env
    return mix * (peak / np.max(np.abs(mix)))


def render_sequence(steps, step_duration=1.0, ring=1.5, peak=0.8):
    """Render a sequence of chords one after another, each ringing on under the
    next: [[60], [67]] is a melodic fifth, [[60, 64, 67]] a single triad."""
    step_n = int(step_duration * SAMPLE_RATE)
    parts = [render(chord, duration=step_duration + ring, peak=1.0) for chord in steps]
    mix = np.zeros(step_n * (len(steps) - 1) + len(parts[-1]))
    for i, part in enumerate(parts):
        mix[i * step_n : i * step_n + len(part)] += part
    return mix * (peak / np.max(np.abs(mix)))


def write_mp3(samples, path):
    """Encode mono float samples to MP3 via lame (tags stripped for reproducibility)."""
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(
        ["lame", "--quiet", "-r", "-s", str(SAMPLE_RATE / 1000), "--bitwidth", "16",
         "--signed", "--little-endian", "-m", "m", "-V", "4", "-t", "--noreplaygain",
         "-", path],
        input=pcm, check=True,
    )
