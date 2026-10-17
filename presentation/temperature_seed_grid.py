"""Temperature x seed accuracy grid on a slice of MATH-500 (Ch. 4 follow-up).

Question: is temperature really that sensitive, or is single-run noise
(one sampled token flips -> the whole continuation diverges) doing most
of the work? Run every (temperature, seed, problem) cell, then compare
the spread *across seeds* at a fixed T with the spread *across T*.

Reuses the book's own pieces: load_model_and_tokenizer, render_prompt,
generate_text_top_p_stream_cache, extract_final_candidate, grade_answer.

Usage (from the repo root, on the GPU machine):

    # one GPU, everything
    uv run python presentation/temperature_seed_grid.py --device cuda:0

    # split temperatures across GPUs (three terminals), then summarize
    uv run python presentation/temperature_seed_grid.py --device cuda:0 --temps 0 0.3 0.5
    uv run python presentation/temperature_seed_grid.py --device cuda:1 --temps 0.7 0.9
    uv run python presentation/temperature_seed_grid.py --device cuda:2 --temps 1.1 1.5
    uv run python presentation/temperature_seed_grid.py --summarize

Results are appended to presentation/temperature_grid_runs/*.jsonl, one
line per generation, so an interrupted run resumes where it stopped.
"""

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch

from reasoning_from_scratch.ch03 import (
    load_model_and_tokenizer,
    load_math500_test,
    render_prompt,
    extract_final_candidate,
    grade_answer,
)
from reasoning_from_scratch.ch04 import (
    generate_text_stream_concat_flex,
    generate_text_top_p_stream_cache,
)

REPO = Path(__file__).resolve().parents[1]
# Reuse the weights the Ch. 4 notebook already downloaded (no second copy)
MODEL_DIR = REPO / "ch04" / "01_main-chapter-code" / "qwen3"
MATH500_PATH = REPO / "ch03" / "01_main-chapter-code" / "math500_test.json"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "temperature_grid_runs"


def cell_seed(seed, problem_idx):
    # Each (seed, problem) cell gets its own RNG state, independent of run
    # order. The same seed is reused across temperatures on purpose: that is
    # exactly the "same seed, slightly different T" setup from the notebook.
    return seed * 10_000 + problem_idx


def load_done(out_dir):
    done = set()
    for path in out_dir.glob("*.jsonl"):
        with path.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done.add((r["temperature"], r["seed"], r["problem_idx"]))
    return done


def run_grid(args):
    out_dir = args.out_dir
    out_dir.mkdir(exist_ok=True)
    done = load_done(out_dir)

    math_data = load_math500_test(local_path=MATH500_PATH)[:args.n_problems]
    device = torch.device(args.device)
    model, tokenizer = load_model_and_tokenizer(
        which_model=args.model, device=device,
        use_compile=False, local_dir=MODEL_DIR,
    )

    # Greedy (T=0) is deterministic, so one "seed" is enough
    jobs = [
        (t, s, i)
        for t in args.temps
        for s in (args.seeds[:1] if t == 0 else args.seeds)
        for i in range(len(math_data))
        if (t, s, i) not in done
    ]
    print(f"{len(jobs)} generations to run ({len(done)} already on disk)")

    out_path = out_dir / f"{args.model}-{args.device.replace(':', '-')}.jsonl"
    start = time.time()
    with out_path.open("a", encoding="utf-8") as f:
        for n, (t, s, i) in enumerate(jobs, start=1):
            row = math_data[i]
            torch.manual_seed(cell_seed(s, i))
            text = generate_text_stream_concat_flex(
                model, tokenizer, render_prompt(row["problem"]), device,
                max_new_tokens=args.max_new_tokens,
                generate_func=generate_text_top_p_stream_cache,
                temperature=t, top_p=args.top_p,
            )
            extracted = extract_final_candidate(text)
            record = {
                "model": args.model,
                "temperature": t,
                "top_p": args.top_p,
                "seed": s,
                "problem_idx": i,
                "gtruth_answer": row["answer"],
                "extracted": extracted,
                "correct": bool(grade_answer(extracted, row["answer"])),
                "num_tokens": len(tokenizer.encode(text)),
                "generated_text": text,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            elapsed = time.time() - start
            eta = elapsed / n * (len(jobs) - n)
            print(f"[{n}/{len(jobs)}] T={t} seed={s} problem={i} "
                  f"correct={record['correct']}  ETA {eta/60:.1f} min",
                  flush=True)


def summarize(out_dir):
    records = []
    for path in out_dir.glob("*.jsonl"):
        with path.open(encoding="utf-8") as f:
            records += [json.loads(line) for line in f]
    if not records:
        print(f"No results in {out_dir}")
        return

    by_t = defaultdict(list)
    for r in records:
        by_t[r["temperature"]].append(r)

    print(f"\n{'T':>5} | {'acc/seed mean':>13} | {'min':>5} | {'max':>5} | "
          f"{'vote acc':>8} | {'distinct ans':>12} | {'avg tok':>7}")
    print("-" * 74)
    rows = []
    for t in sorted(by_t):
        recs = by_t[t]

        # Accuracy of each seed = one full "single run" of the eval
        per_seed = defaultdict(list)
        for r in recs:
            per_seed[r["seed"]].append(r["correct"])
        seed_accs = {s: sum(v) / len(v) for s, v in per_seed.items()}
        accs = list(seed_accs.values())

        # Majority vote across seeds per problem (self-consistency preview).
        # Ties are broken by Counter order, i.e. first answer seen.
        per_problem = defaultdict(list)
        for r in recs:
            per_problem[r["problem_idx"]].append(r)
        vote_correct, distinct = [], []
        for idx, rs in per_problem.items():
            answers = [r["extracted"] for r in rs]
            winner = Counter(answers).most_common(1)[0][0]
            vote_correct.append(grade_answer(winner, rs[0]["gtruth_answer"]))
            distinct.append(len(set(answers)))
        vote_acc = sum(vote_correct) / len(vote_correct)

        avg_tok = statistics.mean(r["num_tokens"] for r in recs)
        print(f"{t:>5} | {statistics.mean(accs):>13.1%} | {min(accs):>5.0%} | "
              f"{max(accs):>5.0%} | {vote_acc:>8.1%} | "
              f"{statistics.mean(distinct):>12.2f} | {avg_tok:>7.0f}")
        rows.append((t, seed_accs, vote_acc))

    # How stable is a single problem across seeds at a fixed T?
    print("\nPer problem: how many seeds got it right (sampled T only)")
    for t in sorted(by_t):
        if t == 0:
            continue
        per_problem = defaultdict(list)
        for r in by_t[t]:
            per_problem[r["problem_idx"]].append(r["correct"])
        always = sum(all(v) for v in per_problem.values())
        never = sum(not any(v) for v in per_problem.values())
        sometimes = len(per_problem) - always - never
        print(f"  T={t}: always {always}, sometimes {sometimes}, never {never}")

    plot(rows, out_dir)


def plot(rows, out_dir):
    import matplotlib.pyplot as plt

    blue, orange = "#2a78d6", "#eb6834"  # dataviz reference palette, slots 1-2
    ink, muted, grid = "#2b2b29", "#6b6a63", "#e6e5e0"

    temps = [t for t, _, _ in rows]
    means = [statistics.mean(a.values()) for _, a, _ in rows]
    votes = [v for _, _, v in rows]

    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for t, accs, _ in rows:
        ax.scatter([t] * len(accs), list(accs.values()), s=36, color=blue,
                   alpha=0.35, edgecolor="none", zorder=2)
    ax.plot(temps, means, color=blue, lw=2, marker="o", ms=6,
            label="single run (mean of seeds; dots = individual seeds)",
            zorder=3)
    ax.plot(temps, votes, color=orange, lw=2, ls="--", marker="o", ms=6,
            label="majority vote across seeds", zorder=3)

    ax.set_xlabel("temperature", color=muted)
    ax.set_ylabel("MATH-500 slice accuracy", color=muted)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=grid, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(grid)
    ax.tick_params(colors=muted)
    ax.set_title("Accuracy vs. temperature (spread across seeds)",
                 color=ink, loc="left")
    ax.legend(frameon=False, labelcolor=ink, fontsize=9)
    fig.tight_layout()

    out = out_dir / "temperature_grid.png"
    fig.savefig(out, dpi=150)
    print(f"\nPlot saved to {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--model", default="base", choices=["base", "reasoning"])
    p.add_argument("--temps", type=float, nargs="+",
                   default=[0.0, 0.3, 0.5, 0.7, 0.9, 1.1, 1.5])
    p.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    p.add_argument("--n-problems", type=int, default=20)
    p.add_argument("--top-p", type=float, default=None,
                   help="None = pure temperature sampling (isolates T's effect)")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                   help="Keep one directory per setting (top-p, max tokens)")
    p.add_argument("--summarize", action="store_true")
    args = p.parse_args()

    if args.summarize:
        summarize(args.out_dir)
    else:
        run_grid(args)
        summarize(args.out_dir)
