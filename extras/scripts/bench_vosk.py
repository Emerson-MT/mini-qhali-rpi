#!/usr/bin/env python3
import argparse
import json
import statistics
import time
import wave
from pathlib import Path

from vosk import Model, KaldiRecognizer


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def decode_once(model: Model, wav_path: Path) -> str:
    with wave.open(str(wav_path), "rb") as wf:
        if wf.getnchannels() != 1:
            raise ValueError("El WAV debe ser mono. Usa ffmpeg -ac 1.")
        if wf.getsampwidth() != 2:
            raise ValueError("El WAV debe ser PCM 16-bit. Usa ffmpeg -sample_fmt s16.")

        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        return result.get("text", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav", type=Path)
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()

    if not args.wav.exists():
        raise FileNotFoundError(args.wav)
    if not args.model_dir.exists():
        raise FileNotFoundError(args.model_dir)

    print(f"Audio: {args.wav}")
    print(f"Modelo: {args.model_dir}")

    audio_s = wav_duration(args.wav)
    print(f"Duración audio: {audio_s:.3f} s")

    t0 = time.perf_counter()
    model = Model(str(args.model_dir))
    load_s = time.perf_counter() - t0
    print(f"Tiempo carga modelo: {load_s:.3f} s")

    times = []
    transcript = decode_once(model, args.wav)  # warm-up

    for i in range(args.repeat):
        t0 = time.perf_counter()
        transcript = decode_once(model, args.wav)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        print(f"run={i+1} elapsed={elapsed:.3f}s RTF={elapsed/audio_s:.3f}")

    mean_s = statistics.mean(times)
    stdev_s = statistics.stdev(times) if len(times) > 1 else 0.0

    print("\n=== Resultado ===")
    print(f"Texto: {transcript}")
    print(f"mean_elapsed_s={mean_s:.3f}")
    print(f"stdev_elapsed_s={stdev_s:.3f}")
    print(f"audio_s={audio_s:.3f}")
    print(f"RTF_mean={mean_s/audio_s:.3f}")
    print(f"faster_than_realtime={mean_s < audio_s}")


if __name__ == "__main__":
    main()
