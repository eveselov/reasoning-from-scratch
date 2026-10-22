# presentation/temperature_seed_grid Script

**How it works:**
- It reuses the book's own functions (`load_model_and_tokenizer`, `render_prompt`, `generate_text_top_p_stream_cache`, `extract_final_candidate`, `grade_answer`), so it's the Ch. 4 code wrapped in a loop.
- It runs every combination of temperature × seed × problem on the first N MATH-500 problems. By default that's 7 temperatures (0 to 1.5), 5 seeds, 20 problems and 512 max tokens.
- T=0 (greedy decoding) gives the same answer whatever the seed, so it runs only once as a baseline.
- Each (seed, problem) pair gets its own fixed random seed, and the same one is used at every temperature. That's the "same seed, slightly different T" situation you were seeing in the notebook.
- Top-p is off by default, so you see the effect of temperature alone. To compare, run again with `--top-p 0.9 --out-dir presentation/grid_top_p` and keep each setting in its own directory.
- Each generation is saved as soon as it finishes, so if the run is interrupted it picks up where it stopped. These results files and the plot are ignored by git (`*.jsonl`, `*.png` in `.gitignore`); only the script is tracked.

**What it reports for each temperature:**
- **Accuracy per seed (mean, min, max):** the min-to-max range is the "great variability" you noticed, now measured. Compare it with how much the mean moves between temperatures.
- **Majority-vote accuracy across seeds:** a preview of self-consistency.
- **Distinct answers per problem** and **average tokens**: higher temperature gives more varied answers and longer, rambling output.
- **For each problem, how often the seeds agree:** "always / sometimes / never" right. The "sometimes" group holds the problems where a single run tells you little.
- **A plot** of accuracy against temperature, with each seed as a dot.

**Running it** (from the repo root):
```bash
PYTHONIOENCODING=utf-8 uv run python presentation/temperature_seed_grid.py --device cuda:0
```
In PowerShell, run `$env:PYTHONIOENCODING='utf-8'` first. Without it, the book's download helper crashes when output is piped or redirected, because the Windows console encoding can't print the `✓` it uses.

On the smoke test, each generation took about 1 second at 128 tokens. With the defaults (620 generations, up to 512 tokens) I'd expect roughly 30–40 minutes on one GPU. Your ASUS currently sleeps after 60 minutes, so the sleep fix from your open items is worth applying first.

**Only GPU 0 is visible:** `nvidia-smi` in this session listed only one card, not four. The docstring's example of splitting temperatures across `cuda:0/1/2` won't work until all the GPUs show up, perhaps because of a `CUDA_VISIBLE_DEVICES` setting or how the session was started. A single GPU is fine for this size of run anyway.

**Results from the tiny test** (3 problems, 2 seeds, 128 tokens):
- T=0 and T=0.7 each scored 1 out of 3.
- T=1.5 scored 0 and its outputs were twice as long, which is the high-temperature drift starting to show.

That's too small to conclude anything; the full grid is where the flat-range pattern should show up (or not). Once the run finishes, it'd be worth writing down what you see in `my-notes/Ch04.md`. The plot is also a good candidate for a slide in the talk.