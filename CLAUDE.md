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

- **Now**: Surface Studio (this machine). No serious GPU — fine for
  Chapters 1–4 (inference, evaluation, inference-time scaling) which the
  book says run reasonably on CPU.
- **Later**: I'll switch to a 4-GPU machine once a chapter actually needs
  it — that's realistically Ch. 5 onward (self-refinement) and definitely
  Ch. 6–8 (RL/GRPO training, distillation), per the book's own hardware
  guidance in the README.
- When I switch, I'll `git clone` this fork (my origin) to the new machine
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

## Progress (update this as I go)

Status values: `not started` / `reading` / `code reviewed` / `done`.

| Chapter | Topic                                        | Status      | Notes |
|---------|-----------------------------------------------|-------------|-------|
| 1       | Understanding Reasoning Models (no code)      | not started |       |
| 2       | Generating Text with a Pre-trained LLM        | not started |       |
| 3       | Evaluating Reasoning Models                   | not started |       |
| 4       | Improving Reasoning with Inference-Time Scaling | not started |     |
| 5       | Inference-Time Scaling via Self-Refinement    | not started |       |
| 6       | Training Reasoning Models with RL             | not started |       |
| 7       | Improving GRPO for RL                         | not started |       |
| 8       | Distilling Reasoning Models                   | not started |       |
| App C   | Qwen3 LLM Source Code                         | not started |       |
| App D   | Using Larger LLMs                             | not started |       |
| App E   | Batching / Throughput                         | not started |       |
| App F   | Common Approaches to LLM Evaluation           | not started |       |
| App G   | Building a Chat Interface                     | not started |       |

## Open items / reminders to self

- (nothing yet — add running to-dos here, e.g. "ask Claude to explain GRPO
  advantage estimation once I hit ch07")
