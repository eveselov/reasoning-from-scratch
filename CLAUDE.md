# CLAUDE.md — personal reading/learning project

This file tells Claude Code what this repo is *for me*, so it can help
appropriately across sessions and across machines. Update the "Progress"
section as I move through the book — that's the part that goes stale.

## What this repo is

A personal fork (`eveselov/reasoning-from-scratch`, origin) of Sebastian
Raschka's official code repo for *Build a Reasoning Model (From Scratch)*
(Manning; upstream: `rasbt/reasoning-from-scratch`). It is not a from-scratch
project of my own — the book's code is the reference material I'm studying.

## My plan, in my own words

1. **Learn**: read the physical/paper book chapter by chapter, and go
   through the matching notebook/code in this repo line by line as I go —
   not ahead of where I am in the book.
2. **Teach**: prepare a presentation for friends, illustrated with one or
   more notebooks that are *shortened, simplified* versions of the book's
   code — enough to demo the idea in a talk, not full reproductions.
3. **Review**: write an Amazon review of the book once I've gone through
   enough of it, to support Raschka's work. I want to collect impressions
   and standout details chapter-by-chapter rather than trying to remember
   everything at the end.

## Hardware / machine situation

- **Surface Studio**: No serious GPU — fine for
  Chapters 1–4 (inference, evaluation, inference-time scaling) which the
  book says run reasonably on CPU.
- **GPU machine (ASUS, Windows 11, headless via RDP/SSH)**: 4× Quadro RTX
  8000 (48 GB, Turing sm_75), reinstalled 2026-10-18. On a normal 15 A home
  circuit, so all 4 are capped at 150 W by a startup task ("GPU power cap
  150W", `nvidia-smi -pl 150`). Metered 2026-10-23 (socket also feeds the
  Surface + printer): idle 200 W; each loaded GPU adds ~165 W at the wall;
  all 4 GPUs 869 W; all 4 + CPU 100% 940 W (~65% of the 1,440 W continuous
  limit). Uncapped would be ~1.44 kW, at the limit. Capped, each card keeps
  ~60% of its speed; no thermal throttling. Xeon W-2195,
  256 GB RAM. Needed realistically from Ch. 5 onward (self-refinement) and
  definitely Ch. 6–8 (RL/GRPO training, distillation), per the book's own
  hardware guidance in the README.
  - PyTorch: `pyproject.toml` has a local Windows rule that pulls the
    cu128 PyTorch build (upstream's default was CPU-only). Keep it when
    merging upstream.
  - Turing has no native bf16 support, so prefer fp16/fp32. Windows has no
    NCCL, so multi-GPU falls back to gloo; consider WSL2 if a later
    chapter needs fast multi-GPU training.
  - `torch.compile` / `--compile` is a no-op on this machine: the compiler
    skips bf16 on Turing, and Triton isn't installed on Windows. Book
    speedups from compiling won't reproduce here; that's expected.
  - Layout (nvidia-smi / PCI order; set `CUDA_DEVICE_ORDER=PCI_BUS_ID` so
    PyTorch numbers them the same): GPUs 0–2 TCC, GPU 3 (bus 0x68) WDDM,
    rendering the RDP desktop. The driver forces one card to stay WDDM —
    asking for all 4 TCC flips GPU 3 back after reboot.
  - NVLink: both bridges active, but only 0↔1 is usable (43.7 GiB/s);
    2↔3 peer copies are blocked by GPU 3's WDDM mode (9.4 GiB/s via PCIe).
    GPU choice: default `cuda:0`; for 2 GPUs use `0,1`.
  - If a GPU shows Code 43 after boot (happened once, 2026-10-18), admin:
    `pnputil /restart-device "<instance id from Device Manager>"`.
  - Network: wired Ethernet (Intel X550, 1 Gbps). Don't go back to the
    Realtek 8812BU USB Wi-Fi dongle — it dropped all traffic for 7–9 s at
    a time, which froze the RDP session for ~30 s (diagnosed 2026-10-11).
- When I switch machines, I'll `git clone` this fork (my origin) to the new machine
  — including my notes, presentation material, and review draft below, since
  those live in this repo, not just on this laptop. **Don't assume anything
  I want kept lives outside git** — if it matters, it should be a tracked
  file here.

## Git remotes

- `origin` → my fork (`eveselov/reasoning-from-scratch`) — where I push.
- `upstream` → the official book repo (`rasbt/reasoning-from-scratch`) —
  added so I can pull in any fixes/updates Raschka makes while I'm reading.
  Not fetched/merged automatically; when I want the latest:
  ```bash
  git fetch upstream
  git merge upstream/main        # or: git rebase upstream/main
  ```

## Personal directories (mine, not upstream's)

These don't exist in the upstream book repo — create them as needed:

- `my-notes/chXX.md` — one file per chapter, my own reading notes,
  questions, "ask Claude about this" flags. Write these *as I finish a
  chapter*, not in advance.
- `presentation/` — slide outline + the condensed teaching notebook(s) for
  the friends talk. Keep these deliberately small/runnable — the goal is a
  live demo, not chapter fidelity.
- `review/notes.md` — running scratch notes for the eventual Amazon review,
  one section per chapter (what stood out, what was confusing, comparisons
  to the companion *LLMs From Scratch* book). Draft the actual review text
  near the end from these.

## How to help me

- **Follow, don't lead.** I'm reading the paper book in order. Don't jump
  ahead to later chapters' code/concepts unless I ask — treat later
  chapters as spoilers.
- When I say "I just finished chapter N," a good default is: open that
  chapter's main notebook with me, walk through it against what the book
  said, and flag anything in the code that's subtler than the prose
  suggests.
- When asked for the **presentation notebooks**: prefer trimming/simplifying
  the book's actual code (fewer epochs, smaller model/data, cut boilerplate)
  over writing new from-scratch examples — the point is "here's what the
  book does," compressed.
- When asked for **review help**: pull concrete details from the specific
  chapter/code we've covered rather than generic praise — specificity is
  what makes a review useful to other readers.
- I'm on Windows (PowerShell + Git Bash available). Mention when a book
  instruction assumes Linux/macOS and needs a Windows equivalent — see also
  the repo's own [troubleshooting.md](troubleshooting.md) and
  [ch02/02_setup-tips](ch02/02_setup-tips) before improvising.
- Large training/GPU-heavy runs (RL/GRPO in ch06–07, distillation in ch08)
  aren't expected to actually run on the Surface Studio — treat requests
  there as "explain / prep for later / run a tiny smoke-test," not "run the
  real thing," until I say I'm on the GPU machine.

## Working across chat threads

- New thread per work session/topic (a chapter walkthrough, presentation
  prep, review drafting) rather than one endless thread — a new thread does
  *not* automatically carry over a prior thread's conversation history.
- What *does* carry over automatically: this file, in full, every session.
  Claude's own separate persistent-memory notes (durable facts/preferences
  it has chosen to save about this project) also carry over automatically.
- What does *not* carry over automatically: `my-notes/`, `presentation/`,
  `review/notes.md`. They persist in git, but Claude only reads them when
  asked or when obviously relevant — so when starting a new thread on
  chapter N, say so (or point at `my-notes/chNN.md`) to load the right file.
- End-of-session habit: update the Progress table and Open items below
  before closing a thread, so the next thread — even a brand-new one —
  starts oriented without re-explaining.

## How Claude should update this file

When something changes that belongs here (a chapter finished, a new open
item, a new convention we agree on) — propose the edit and show me the
diff, then wait for my go-ahead before applying it. Don't edit this file
silently, and don't wait for me to explicitly say "update CLAUDE.md" either
— noticing it's needed and proposing it is the expected behavior.

## Progress (update this as I go)

Status values: `not started` / `reading` / `code reviewed` / `done`.

| Chapter | Topic                                        | Status      | Notes |
|---------|-----------------------------------------------|-------------|-------|
| 1       | Understanding Reasoning Models (no code)      | done        |       |
| 2       | Generating Text with a Pre-trained LLM        | done        |       |
| 3       | Evaluating Reasoning Models                   | done        |       |
| 4       | Improving Reasoning with Inference-Time Scaling | done        |     |
| 5       | Inference-Time Scaling via Self-Refinement    | reading     | book read; notebooks next |
| 6       | Training Reasoning Models with RL             | not started |       |
| 7       | Improving GRPO for RL                         | not started |       |
| 8       | Distilling Reasoning Models                   | not started |       |
| App C   | Qwen3 LLM Source Code                         | not started |       |
| App D   | Using Larger LLMs                             | not started |       |
| App E   | Batching / Throughput                         | not started |       |
| App F   | Common Approaches to LLM Evaluation           | not started |       |
| App G   | Building a Chat Interface                     | not started |       |

## Open items / reminders to self

- ASUS sleep: default is manual sleep (Start → Sleep, wake with front
  button) with a 4 h auto-sleep as a safety net. Runs don't count as
  activity — before a long job, admin: `powercfg /change
  standby-timeout-ac 0`; restore after with `... 240`.
- ASUS SSH: `sshd` installed 2026-10-18 (auto-start, survives sleep and
  reboot); `ssh user@ASUS-GPU` from the Surface works with a password;
  shell is cmd.exe (DefaultShell left unset — PowerShell 7 isn't
  installed). Still to do: key login ([BUILD.md](BUILD.md) §3, admin
  account → `administrators_authorized_keys`), VS Code Remote-SSH (§5).
