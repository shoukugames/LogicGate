#!/usr/bin/env python3
"""Synthesise every sound in the game into assets/audio/*.wav.

Run this only when the sound design changes (needs numpy; the game itself does not).
All music is original and generated here: slow ambient pads, soft bells and a
synthetic reverb, rendered as seamless loops.
"""
import os
import wave

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "audio")
RNG = np.random.default_rng(20261104)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def save(name, data, rate):
    """data: float array, mono (n,) or stereo (n, 2), range about -1..1"""
    data = np.asarray(data, dtype=np.float64)
    if data.ndim == 1:
        data = data[:, None]
    peak = np.max(np.abs(data)) or 1.0
    data = data / peak * 0.89
    pcm = (data * 32767).astype("<i2")
    with wave.open(os.path.join(OUT, name), "wb") as handle:
        handle.setnchannels(pcm.shape[1])
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm.tobytes())
    print(f"{name}: {len(pcm) / rate:.1f}s")


def lowpass(signal, rate, cutoff):
    spec = np.fft.rfft(signal, axis=0)
    freqs = np.fft.rfftfreq(signal.shape[0], 1 / rate)
    curve = 1 / (1 + (freqs / cutoff) ** 4)
    if signal.ndim == 2:
        curve = curve[:, None]
    return np.fft.irfft(spec * curve, n=signal.shape[0], axis=0)


def circular_reverb(signal, rate, seconds=4.0, mix=0.55, seed=1):
    """Convolve with decaying noise, wrapping the tail so the loop stays seamless."""
    rng = np.random.default_rng(seed)
    n = signal.shape[0]
    out = np.zeros((n, 2))
    length = int(seconds * rate)
    t = np.arange(length) / rate
    for ch in range(2):
        ir = rng.standard_normal(length) * np.exp(-t * 6.9 / seconds)
        ir = lowpass(ir, rate, 3500)
        ir[: int(0.012 * rate)] *= np.linspace(0, 1, int(0.012 * rate))
        ir /= np.sqrt(np.sum(ir ** 2))
        size = n  # circular convolution over exactly one loop length
        wet = np.fft.irfft(np.fft.rfft(signal[:, ch], size) * np.fft.rfft(ir, size), size)
        out[:, ch] = signal[:, ch] * (1 - mix) + wet * mix * 1.6
    return out


def envelope(n, rate, attack, release):
    env = np.ones(n)
    a = min(n, max(1, int(attack * rate)))
    r = min(n - a, max(1, int(release * rate)))
    env[:a] = np.linspace(0, 1, a) ** 2
    env[n - r:] *= np.linspace(1, 0, r) ** 2
    return env


def pad_voice(m, seconds, rate, bright=1.0):
    n = int(seconds * rate)
    t = np.arange(n) / rate
    out = np.zeros(n)
    for detune in (-0.07, 0.0, 0.08):
        f = midi_hz(m + detune)
        phase = RNG.uniform(0, 2 * np.pi)
        # soft saw from a few harmonics
        for h, amp in ((1, 1.0), (2, 0.42 * bright), (3, 0.2 * bright), (4, 0.09 * bright), (5, 0.05 * bright)):
            out += amp * np.sin(2 * np.pi * f * h * t + phase * h)
    lfo = 1 + 0.18 * np.sin(2 * np.pi * RNG.uniform(0.07, 0.15) * t + RNG.uniform(0, 6))
    return out * lfo * envelope(n, rate, seconds * 0.35, seconds * 0.45) / 3


def bell(m, seconds, rate, decay=2.2):
    n = int(seconds * rate)
    t = np.arange(n) / rate
    f = midi_hz(m)
    out = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)
           + 0.18 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6))
    env = np.exp(-t * decay)
    env[: int(0.004 * rate)] *= np.linspace(0, 1, int(0.004 * rate))
    return out * env


def place(buffer, sound, start, gain=1.0, pan=0.0):
    """Add a mono sound into a stereo loop buffer, wrapping around the end."""
    n = buffer.shape[0]
    left = gain * np.sqrt((1 - pan) / 2)
    right = gain * np.sqrt((1 + pan) / 2)
    idx = (np.arange(len(sound)) + start) % n
    np.add.at(buffer[:, 0], idx, sound * left)
    np.add.at(buffer[:, 1], idx, sound * right)


def ambient_track(rate, chords, chord_seconds, scale, bells_per_chord, root_bass, seed, bright):
    global RNG
    RNG = np.random.default_rng(seed)
    total = len(chords) * chord_seconds
    n = int(total * rate)
    buf = np.zeros((n, 2))
    overlap = 2.5
    for i, chord in enumerate(chords):
        start = int((i * chord_seconds - overlap / 2) * rate)
        for j, m in enumerate(chord):
            voice = pad_voice(m, chord_seconds + overlap, rate, bright)
            place(buf, voice, start, 0.16, pan=(j / max(1, len(chord) - 1)) * 1.2 - 0.6)
        bass = pad_voice(root_bass[i], chord_seconds + overlap, rate, 0.3)
        place(buf, bass, start, 0.22, 0.0)
        # gentle bells drawn from the scale, never crowded
        times = np.sort(RNG.uniform(0.3, chord_seconds - 0.5, bells_per_chord))
        for k, tm in enumerate(times):
            note = int(RNG.choice(scale))
            place(buf, bell(note, 4.5, rate, decay=RNG.uniform(1.2, 2.0)),
                  int((i * chord_seconds + tm) * rate), RNG.uniform(0.05, 0.09), RNG.uniform(-0.7, 0.7))
    # a soft wind-like noise bed
    noise = lowpass(RNG.standard_normal((n, 2)), rate, 500)
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / n * 3)[:, None]
    buf += noise * 0.012 * swell
    buf = lowpass(buf, rate, 5200)
    return circular_reverb(buf, rate, seconds=5.0, mix=0.5, seed=seed)


def music():
    rate = 22050
    # Title: C major colours, airy
    chords = [[60, 64, 67, 71], [57, 60, 64, 67, 71], [53, 57, 60, 64], [55, 59, 62, 67],
              [52, 55, 59, 64], [57, 60, 64, 69], [53, 57, 60, 65, 69], [55, 60, 62, 67]]
    bass = [36, 33, 29, 31, 28, 33, 29, 31]
    scale = [72, 74, 76, 79, 81, 84, 86, 88]
    save("bgm_title.wav", ambient_track(rate, chords, 6, scale, 3, bass, 11, 0.9), rate)
    # Puzzle: D lydian-ish, slower and calmer so it stays out of the way
    chords = [[62, 66, 69, 73], [64, 67, 71, 74], [59, 62, 66, 69, 73], [55, 59, 62, 66],
              [62, 66, 69, 76], [57, 61, 64, 68], [59, 62, 66, 71], [55, 59, 64, 67]]
    bass = [38, 40, 35, 31, 38, 33, 35, 31]
    scale = [74, 76, 78, 81, 83, 86, 88, 90]
    save("bgm_game.wav", ambient_track(rate, chords, 8, scale, 2, bass, 23, 0.7), rate)


def tone(freq, seconds, rate, wave_kind="sine", decay=8.0, attack=0.003):
    n = int(seconds * rate)
    t = np.arange(n) / rate
    f = np.asarray(freq) if np.ndim(freq) else np.full(n, freq)
    phase = 2 * np.pi * np.cumsum(f) / rate
    if wave_kind == "sine":
        s = np.sin(phase)
    elif wave_kind == "tri":
        s = 2 / np.pi * np.arcsin(np.sin(phase))
    elif wave_kind == "square":
        s = np.tanh(np.sin(phase) * 4)
    else:
        s = np.sin(phase) + 0.3 * np.sin(2 * phase)
    env = np.exp(-t * decay)
    a = max(1, int(attack * rate))
    env[:a] *= np.linspace(0, 1, a)
    return s * env


def effects():
    rate = 44100

    def cat(*parts):
        return np.concatenate(parts)

    def silence(s):
        return np.zeros(int(s * rate))

    def mix(*sounds):
        n = max(len(s) for s in sounds)
        out = np.zeros(n)
        for s in sounds:
            out[: len(s)] += s
        return out

    def stereo(mono, verb=0.25):
        pad = np.concatenate([mono, np.zeros(int(0.6 * rate))])
        st = np.stack([pad, pad], axis=1)
        rng = np.random.default_rng(5)
        length = int(0.5 * rate)
        t = np.arange(length) / rate
        out = st.copy()
        for ch in range(2):
            ir = rng.standard_normal(length) * np.exp(-t * 12)
            ir /= np.sqrt(np.sum(ir ** 2))
            wet = np.convolve(pad, ir)[: len(pad)]
            out[:, ch] = pad * (1 - verb) + wet * verb
        return out

    save("click.wav", stereo(tone(1250, 0.06, rate, decay=60) * 0.6, 0.1), rate)
    save("hover.wav", tone(2200, 0.03, rate, decay=120) * 0.3, rate)
    sweep = np.linspace(500, 900, int(0.12 * rate))
    save("pickup.wav", stereo(tone(sweep, 0.12, rate, "tri", decay=20)), rate)
    thunk = tone(np.linspace(220, 120, int(0.15 * rate)), 0.15, rate, "sine", decay=25)
    snap = tone(3000, 0.03, rate, decay=150) * 0.4
    save("drop.wav", stereo(mix(thunk, snap)), rate)
    save("remove.wav", stereo(tone(np.linspace(700, 300, int(0.14 * rate)), 0.14, rate, "tri", decay=18)), rate)
    save("switch.wav", stereo(mix(tone(1800, 0.02, rate, decay=200), cat(silence(0.03), tone(2600, 0.025, rate, decay=180))) * 0.8, 0.1), rate)
    save("flip.wav", stereo(cat(tone(900, 0.05, rate, decay=40), tone(1200, 0.07, rate, decay=40))), rate)
    err = cat(tone(311, 0.16, rate, "tri", decay=6), tone(233, 0.3, rate, "tri", decay=6))
    save("error.wav", stereo(err), rate)
    save("tick.wav", tone(1600, 0.05, rate, "sine", decay=70) * 0.7, rate)
    notes = [72, 76, 79, 84]
    seq = mix(*[cat(silence(i * 0.09), tone(midi_hz(m), 0.9, rate, "bell", decay=4)) for i, m in enumerate(notes)])
    save("success.wav", stereo(seq, 0.35), rate)
    notes = [67, 72, 76, 79, 84, 88]
    seq = mix(*[cat(silence(i * 0.11), tone(midi_hz(m), 1.4, rate, "bell", decay=3)) for i, m in enumerate(notes)],
              cat(silence(0.55), tone(midi_hz(60), 1.6, rate, "tri", decay=2) * 0.5))
    save("level_complete.wav", stereo(seq, 0.4), rate)
    notes = [67, 63, 60, 55]
    seq = mix(*[cat(silence(i * 0.22), tone(midi_hz(m), 0.6, rate, "tri", decay=4)) for i, m in enumerate(notes)])
    save("time_up.wav", stereo(seq, 0.4), rate)
    # Buzzer: a loopable 1 second piezo tone with a little warble
    n = rate
    t = np.arange(n) / rate
    buzz = np.tanh(np.sin(2 * np.pi * 440 * t) * 3) * 0.6 + 0.2 * np.sin(2 * np.pi * 880 * t)
    buzz *= 0.85 + 0.15 * np.sin(2 * np.pi * 8 * t)
    save("buzz.wav", lowpass(buzz, rate, 2600), rate)
    # Motor: loopable whir
    whir = (np.sin(2 * np.pi * 120 * t) * 0.5 + np.sin(2 * np.pi * 240 * t) * 0.3
            + lowpass(np.random.default_rng(3).standard_normal(n), rate, 900) * 0.25)
    whir *= 0.8 + 0.2 * np.sin(2 * np.pi * 30 * t)
    save("motor.wav", whir, rate)
    save("start.wav", stereo(mix(tone(midi_hz(64), 0.5, rate, "bell", decay=5),
                                 cat(silence(0.1), tone(midi_hz(71), 0.7, rate, "bell", decay=4))), 0.35), rate)
    save("new_record.wav", stereo(mix(*[cat(silence(i * 0.08), tone(midi_hz(m), 0.8, rate, "bell", decay=4))
                                        for i, m in enumerate([72, 79, 84, 88, 91])]), 0.4), rate)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    effects()
    music()
