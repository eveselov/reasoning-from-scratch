# Notes for the book review

**This file contains running scratch notes for the eventual Amazon review, one section per chapter.
The actual review text will be derived from tehse notes near the end  of the work.**

# Chapter 1. Understanding Reasoning Models

No code in this chapter — notes are purely about the prose/concepts.

**What stood out:**
- Definitions are consistently sharp and jargon-free, e.g. "reasoning refers
  to a model generating intermediate steps before producing its final
  answer," and the distinction between chain-of-thought reasoning (LLM
  reasoning autoregressively via statistical patterns) vs. traditional
  deterministic reasoning (strict, rule-based steps). No-BS concept
  definitions are a recurring strength so far.
- The three-way taxonomy of reasoning-enhancement methods is a useful
  mental model to carry into the rest of the book:
  1. Inference-time compute scaling (chain-of-thought, sampling) — fixed
     weights, no training.
  2. Reinforcement learning — trial-and-error from environment/human
     feedback.
  3. Distillation — larger "teacher" model to smaller "student" model via
     supervised fine-tuning.
- GPT-4.5's ability to judge *when* extended reasoning is worth it ("reasoning
  is not always necessary or desirable") was called out as its own
  essential capability, not just a footnote.

**Comparisons to *LLMs From Scratch* (companion book):**
- The hands-on, code-first approach is what I valued most in the previous
  book, and it's exactly what I'm hoping carries over here.

**Points of confusion / questions raised while reading:**
- The framing "basic LLM is pattern recognition; reasoning is an agent that
  breaks a task into steps and recovers from mistakes" felt oversimplified
  on first read, though probably captures the essential distinction.
- Expected chapter 1 to introduce agent-building techniques around LLMs;
  it turned out reasoning here means something more fundamental (the
  4-step book roadmap: load pretrained LLM → evaluation → inference-time
  techniques → training-based techniques), with agent orchestration
  pushed out to an appendix. Worth revisiting once that appendix is read.
- Open question on pretraining/post-training/mid-training: whether the
  split is philosophically meaningful or just a practical/resource
  distinction (draft analogy: pretraining ~ evolutionarily acquired
  skills, post-training ~ school-taught specialization).

**Side idea worth keeping in mind for later chapters:**
- Letting a model generate longer output effectively extends how much
  "recurrent" reasoning it can do within one inference call, since later
  forward passes can condition on tokens produced by earlier ones — a way
  around the fixed-depth transformer architecture that isn't obvious from
  the architecture alone.

**Metaphor ideas for review**

Pretraining feels philosophically closer to evolution than to individual
learning: both are the costly, slow process that has to build a general
capacity to learn and reason *before* anything useful can happen — a
randomly initialized transformer, like a brain with no evolutionary
wiring, can't act or learn at all. Post-training/fine-tuning is the
cheap, fast step on top — closer to an individual's education and
life experience, layering specific facts and specialized skills onto
that general capacity.

---

# Chapter 2. Preparing Input Text for LLM

Sebastian pleasantly surprizes me again and again. I thought I have
some general understanding of how models, agents, chats work and
expected to see more details of that in Raschka's book. Surprizingly,
I found a competely new (for me) discourse. Even though all the concepts
(rokenizers, models, pretrainin, fine-tuning) have already been familiar
and expected, the very style of presentation was fresh and inspiring
to lean new twists and perspective in the area.

## More than expected

The material of ch02 looked as familiar for me from the previous Raschka's book: 
start with tokenizer, then loading a pretrained model then implement and play with text 
generation function. Nevertheless working with this familiar material in the excellent Raschka's
presentation was very delightful and useful. I learned a few technical styles and tools (uv,
jupyter lab), learned about variety of pretrained models and some phylosophy behind them,
had to learn GPU characteristics and configurations (I own ASUS with 4 GPUs, but knew little about it).
I refreshed my understanding of KQV attention mechanism (Raschka provides references to good
relevant articles). I really enjoyed learning playing with KV caching - a very elegant
and straightforward optimization technique, which should have come to my mind when I first learned it,
but it haven't. In my experiments with Raschka's repository on several of my machines
(with and without GPUs) I learned a lot about appropriate settings and caveats of 
concurrent development on different reopsitory clones. I side-jumed to Appendix G and Appendix C,
spent some time with them and found quite useful material (leaving C alone for now for diving later).
Just the process of reading and playing with Raschka's material inspired a lot of
side ideas which I am planning to explore later for myself.

## Appendix G

Side looked at apendix G which promised an internal structure os "an agent".
Looks ver ineresting. Now I am torn - whether to dive into those agent, chat, chainlit(!),
or continue the primary flow of Chapter 2.

## Appendix C

Another pleasant free gift - a well documented Qwen3 source code (Raschka's own reimplementation)

## Exceptional Professionalism

This book is really a piece of art. Art of story telling, art of technical explanation, art of programming.
You can use the book from multiple perspectives - read it in paper, then switch to a notebook
from git, or create a copy/pasted fragment for a specific topic. And eny of it just works!
You can read the book. You can read
the notebooks. You can read the auxiliary code. You can run any of it. You can use full setup
from the cloned repository, or partial pip- or uv- installed packages. Raschka has thought 
of everything!
In fact the book behaves like a well-polished app that can be used by different
users in different scenarios and configurations - small CPU only laptop or a server with powerful GPUs, 
in base or reasoning or instruc mode - this "app" is well debugged for all permutations.
Knowing from my own developer's experience how difficult is to not just to come to an idea
but to make it really work and work reliably and work for different users - I see that Raschka's
task would be impossible to implement. But here it is. Working! 

## Highly Struictural Guidance

The content of the entire book is systematically illustrated with visualdiagrams representing the overall context, previous and following steps. It is very easy to follow the plot and structure.

## Not everything worked smoothly

The model optimization via python compilation did not work smoothly. Actually,
it did not work at all on one of my Windows computers, and worked fine on another.
Raschka's text warned about potential problems very clearly, so that was expected.
Since it's minor and optional (according to Raschka), I left it alone, 
but will investigate later. The technique itself seems important and useful.

## Exercise Notebook

There are two notebooks in the chapter (as in other chapters) - main and exercise.
For chapter 02 the exercise version is just a subset of the main.
So I was initially confused expecting to find something beyond main
which contains all the same code with a lot of useful expolanatory text.

## CPU/GPU Tradeoffs

Preparing the code Raschka did grea job in a delicate issue of using GPU or CPU in the code.
A general recommendation for this book is using GPU. However since many of the readers
might not have access to it the code is organized so that it runs on CPU only - by default.
It's possible to switch it to GPU, but depending on your hardware that might be tricky.

At the end of the chapter Raschka added a vry useful explanation of model performance
and tradeoffs he has made in the book for users with different machines.
His notes about the pers uncover underlying complexity of this aspects,
which otherwise might escape attention of new readers.

## Chapter Bonus Materials

Apart from the main code in 01_main-chapter-code the ch02 folder of the repository
contains quite a lot of usefiul information - about CPU/GPU usage, torch compilation,
scripts for using the models in different styles. Don't miss them in folders 02_, 03_, 04_, 05_.
Some of them are good Raschka-style articles, others are elegant pieces of code
around the model containing useful patterns.

## Use_model Scripts

I found especially useful three progressively enhcnced scripts for executing requests
on a local Qwen3 model. They are useful both for learning how to implement such sort
of code around the models in the professional elegant Raschka style, and for actual playig with the model.

## Note of Qwen3 caching

After playing with the notebooks and scripts I realized that they create copies
of Qwen3 model in different levels of folder hierarchy. The logic is straigtforward -
qweb3 caching folder is created in in the current folder. I ended up with three of them
(in a notebook, inside ch02, and inside ch02/01_main-chapter_code), 2x1.5GB each.
Not a big deal, but better to know about and act accordingly: e.g. run scripts for ch02
and the following chapters from the root to speed up and save disk memory.

## Minor bug: misleading "tensors are on cpu" warning

Running `ch02/05_use_model/chat_multiturn.py` on my GPU machine prints
`UserWarning: CUDA is available but tensors are on cpu. Memory stats may be 0.`
after every answer, even though generation clearly runs on the GPU.
The cause is a tiny slip in the script: after generation, the collected token IDs
are packed into a new tensor with `torch.tensor(all_token_ids)` (no `device=`),
so that tensor lands on the CPU, and `generate_stats()` warns about it.
The warning is harmless — the printed "Max CUDA memory allocated" figure is still
correct, since it reads the GPU's global counter, not that tensor. One-line fix:
`torch.tensor(all_token_ids, device=device)`. Worth reporting upstream
(`rasbt/reasoning-from-scratch`) as an issue.

For the review: a good example of how small the rough edges are. Even the one
glitch I hit is cosmetic, and the code's own sanity check is what surfaced it.

# Chapter 03. Evaluating Reasoning Models

## Raschka's Presentaion Style

As in his previous book Sebastian uses very structured way of narration.
After presenting a block diaram visual roadmap in the beginning he reuses it
on every section and subsection with comments and highlights illustrating
the current position of the reader in the overall narration - very easy
to stay in context.

## Paper book vs Jupyter Notebook

The book material seems duplicated between the paper book and the notebooks.
I found it very convenient. I start on a sofa reading a chapter, then open
the notebook and go through the same material in a slow pace, carefully reviewing
and understanding every cell. Sometimes I add my own cells for micro experiments.
This is a real "from scratch" style.

## Evaluator Logic - Straightforward

Evaluator logic is quite straightforward. Not being familiar with evaluation patterns
I expected some magic - especially for structured specialized texts like mathematical expressions.
Chapter 03 implements evaluator in a narural simple way. Pleasant surprize not finding
any surprizes. Latex and SymPy syntax normalization is the only "magic".

## Learning

As a very useful side effect of working with the book was learning tools and
techniques I never knew about before: math data sets, math rendering, LaTeX,
(expecting more in the following chapters).

