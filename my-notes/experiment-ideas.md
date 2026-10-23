# Experiment ideas — my own future project (beyond the book)

Ideas that came up while reading the book, mostly Ch04–05 (inference-time
scaling, self-refinement). **Not for the Amazon review** — at most, the
review can mention that the book provokes ideas like these.

References were collected from Claude's memory, not looked up — verify
titles/arXiv IDs before citing.

---

## 1. Motivating thoughts

### Gestalt vs. logic (Ch04, reinforced in Ch05)
- One forward pass = "insight": massive parallel pattern matching, but a
  fixed-depth computation — no loops, limited branching.
- Autoregressive generation = "logic": unlimited iteration, and in an LLM
  the *only* path from the top of the layer stack back to the bottom is
  the sampled token. So the iteration runs through words.
- Sharper version: *"Insight is parallel pattern-matching in one pass;
  reasoning is iteration — and in an LLM the only way to iterate is to
  write something down."*
- Nuances:
  - Words may not reflect the real computation (CoT unfaithfulness).
  - Meaningless filler tokens can help too → language is the *channel* of
    the loop, not necessarily its *content*.
  - Humans have non-verbal working memory; LLMs don't. The metaphor fits
    LLMs better than humans.

### Why only one token per "insight"?
- Not much is thrown away: all layers' hidden states for past positions
  stay in the KV cache and later steps reread them. Only the
  *feedback/commitment* channel is one token wide.
- Hidden states already encode plans beyond the next token (rhyme
  planning, Future Lens).
- One-token commitment as a feature: it collapses ambiguity (you can't
  write two incompatible continuations at once), stops small errors piling
  up (digital vs. analog), and makes training simple and parallel.
- *"The model thinks in paragraphs but speaks in words."*

### Enriching the gestalt directly
- Inject goal/task/situation through something other than prompt text:
  soft prompts, steering vectors, layer modulation, logit-level guidance.
- Non-linguistic context: images/audio/sensor data projected into the
  token-embedding space as "soft tokens."
- Caveat: plain prompts are a strong baseline. Every layer attends to
  them, so "more efficient than the prompt" is not a given.

---

## 2. Experiment roadmap

### Tier A — frozen weights, inference tricks only (Surface, CPU)
Builds on Ch04–05 code: the generation loop, `calc_next_token_logprobas`,
`avg_logprob_answer`, `self_refinement_loop`.

| Experiment | What to build | Notes |
|---|---|---|
| Per-token log-prob / entropy trace | Plot entropy along a generated answer; check whether spikes line up with phrase/step boundaries | Easiest start |
| Entropy-triggered branching | At entropy spikes, fork N continuations (possibly at another temperature) and score them | Mid-sequence version of Ch04 self-consistency; cf. entropix |
| Adaptive stopping / iterations | Decide whether to refine again from the confidence delta | Extends fixed `iterations=2` |
| Classifier-free guidance | Two passes per step (with/without goal line); `uncond + γ·(cond − uncond)`, γ ≈ 1.5–3 | Tests "amplify the goal beyond the prompt" |
| Contrastive decoding | Stronger-model logits minus weaker-model logits (e.g. Qwen3 1.7B − 0.6B) | Two model sizes, still inference-only |
| Activation steering (ActAdd) | Mean hidden-state difference over contrasting prompt pairs; add it back via forward hook on `model.trf_blocks[i]` | Forward passes only, no gradients |
| Soft thinking | Feed back a probability-weighted mix of token embeddings, not the sampled token | Reported to work without training |
| Logit lens | Apply final norm + output head to intermediate layers' hidden states | Analysis: watch the prediction form layer by layer |

### Tier B — cheap training (ASUS, one GPU)
Memory sizing: full fine-tune in fp32 + Adam ≈ 16 bytes/param before
activations → Qwen3-0.6B ≈ 10 GB, 1.7B ≈ 27 GB. Fits on one 48 GB
RTX 8000; no multi-GPU needed. Use fp16/fp32, not bf16 (Turing).

| Experiment | What gets trained | Cost / caveat |
|---|---|---|
| Optimized steering vectors | One vector per layer, trained by gradient descent | Minutes |
| Prompt / prefix tuning | A few dozen soft-token vectors; model frozen | Cheap; weak at small scale per Lester et al. |
| LoRA | Low-rank adapters | Very cheap; book's Qwen3 isn't HF → port LoRA from *LLMs From Scratch* appendix rather than `peft` |
| Multi-token prediction heads | Extra heads on frozen backbone predicting t+2, t+3, … | Cheap (Medusa-1 setup); measures how much "future" the hidden state holds |
| Linear image → LLM projector | One linear layer from frozen CLIP/SigLIP features into Qwen3 embedding space, on image–caption pairs | A few GPU-hours (LLaVA stage 1 / Merullo et al.); cheapest non-linguistic-context test |
| Gist tokens | Fine-tune (LoRA OK) to compress instructions into a few tokens | Moderate; needs an instruction dataset |
| Coconut (continuous thought) | Curriculum fine-tune replacing CoT steps with fed-back hidden states | Moderate; original used GPT-2-sized models |

### Tier C — mostly needs pretraining-scale compute (read, don't run)
- Pause tokens: gains mainly when added during pretraining.
- Recurrent-depth models: generally trained that way from the start.
- Large Concept Models: a new architecture.
- Diffusion LMs: converting an autoregressive model is possible (Gong et
  al. 2024) but a large project.

### Suggested order
1. Entropy trace → entropy-triggered branching (Surface, after notebook
   §5.4–5.6).
2. CFG and ActAdd steering (goal-enrichment idea).
3. Logit lens, whenever curious.
4. ASUS: MTP heads or image projector as the first real training run.
5. Revisit Tier B after book Ch06–08 (they're about further training of
   a pretrained model).

---

## 3. Reading list

### Activation steering / representation engineering
- Subramani, Suresh & Peters 2022 — *Extracting Latent Steering Vectors from Pretrained Language Models* — arXiv:2205.05124
- Turner et al. 2023 — *Steering Language Models With Activation Engineering* (ActAdd) — arXiv:2308.10248 — **start here**
- Rimsky (Panickssery) et al. 2024 — *Steering Llama 2 via Contrastive Activation Addition* — arXiv:2312.06681
- Li et al. 2023 — *Inference-Time Intervention: Eliciting Truthful Answers from a Language Model* — arXiv:2306.03341
- Zou et al. 2023 — *Representation Engineering: A Top-Down Approach to AI Transparency* — arXiv:2310.01405
- Arditi et al. 2024 — *Refusal in Language Models Is Mediated by a Single Direction* — arXiv:2406.11717
- Park, Choe & Veitch 2023 — *The Linear Representation Hypothesis and the Geometry of LLMs* — arXiv:2311.03658
- Anthropic, Templeton et al. 2024 — *Scaling Monosemanticity* (Golden Gate Claude) — transformer-circuits.pub
- Chen et al. 2025 — *Persona Vectors* — arXiv:2507.21509
- Wu et al. 2025 — *AxBench* — prompting often beats steering
- Hands-on: Theia Vogel, *Representation Engineering Mistral-7B an Acid Trip* (blog) + `repeng` library

### Gestalt vs. logic: theory and nuances
- Merrill & Sabharwal 2024 — *The Expressive Power of Transformers with Chain of Thought* (ICLR)
- Feng et al. 2023 — *Towards Revealing the Mystery behind Chain of Thought* (NeurIPS)
- Turpin et al. 2023 — *Language Models Don't Always Say What They Think*
- Pfau et al. 2024 — *Let's Think Dot by Dot* (filler tokens)
- Nisbett & Wilson 1977 — *Telling More Than We Can Know* (human confabulation)
- Fedorenko et al. 2024 — *Language is primarily a tool for communication rather than thought* (Nature)

### Beyond one token per step / latent reasoning
- Anthropic 2025 — *On the Biology of a Large Language Model* (planning ahead)
- Pal et al. 2023 — *Future Lens*
- Gloeckle et al. 2024 — *Better & Faster LLMs via Multi-token Prediction* — arXiv:2404.19737
- Cai et al. 2024 — *Medusa*
- Hao et al. 2024 — *Training LLMs to Reason in a Continuous Latent Space* (Coconut) — arXiv:2412.06769
- Zhang et al. 2025 — *Soft Thinking*
- Geiping et al. 2025 — *Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach* — arXiv:2502.05171
- Dehghani et al. 2018 — *Universal Transformers*
- Goyal et al. 2023 — *Think Before You Speak: Training Language Models with Pause Tokens*
- Meta 2024 — *Large Concept Models* — arXiv:2412.08821
- Nie et al. 2025 — *LLaDA* (diffusion LM); Gong et al. 2024 — AR → diffusion adaptation
- entropix (2024) — entropy/varentropy-based adaptive sampling (GitHub project)

### Enriching context / conditioning
- Lester et al. 2021 — *The Power of Scale for Parameter-Efficient Prompt Tuning*
- Li & Liang 2021 — *Prefix-Tuning*
- Mu et al. 2023 — *Learning to Compress Prompts with Gist Tokens*
- Perez et al. 2018 — *FiLM*
- Borgeaud et al. 2021 — *RETRO*; Wu et al. 2022 — *Memorizing Transformers*
- Sanchez et al. 2023 — *Stay on Topic with Classifier-Free Guidance*
- Li et al. 2022 — *Contrastive Decoding*

### Non-linguistic context (multimodal)
- Tsimpoukelli et al. 2021 — *Frozen* (image as soft prompt to a frozen LM)
- Merullo et al. 2022 — *Linearly Mapping from Image to Text Space*
- Alayrac et al. 2022 — *Flamingo*
- Liu et al. 2023 — *Visual Instruction Tuning* (LLaVA)
- Driess et al. 2023 — *PaLM-E*; Google 2023 — *RT-2*
- Qwen2-Audio, Qwen2.5-Omni (same family as the book's Qwen3)
- Paivio — dual coding theory (human parallel)

---
---
---

# Appendix. Source Conversation with Claude About This Topic

## Me: Reading Chapter 05

I am impressed gain with another surprize: I really did not expect
how much depth can be opened in enhancing the modes=ls without touching their weights.
This exploration reveals a lot about the mechanisms of rationality
both in technical and on philosophical levels.

This time Raschka opened another "obvious" aspect - the model-generated
logits could be not only picked by probabilities, but analyzed to
evaluate aspects of model's self-feeling. This might work like a
self-refelection mechanism, and not only for observation but for
steering the model thinking into specific directions. It is yet another
"discovery" about model reasoning mechanisms.

While reading it I have set aside one after another ideas for my own investigations.
Here are some of them:

- Analyze the sequence of previously generated logits to identify
special turning points in the process of model thinking, such as
ends of statements/phrases or other structural pieces.
- Evaluate the qualizies of such segments in autogenerated sequence,
such as model confidence, relevance, iportance, ...
- Implement non-standard autogenerated strategies other than
linear token predictio. For instance, re-generate a sequence
from a particulat "structural" position with a different
temperaure to make the model more or less inventive; 
re-run from the same point several "branches" of thinking and 
combine them later for a merged continuation; decide when to
stop or continue autogeneration depending on evaluated metrics.

Another thoughht I had while reading this chapter continues
the metaphore realized in the previous chapter - gestalt-vs-logic dichotomy
(forward pass analyses and produces patterns in non-verbal latent form,
autogeneration sequence performs thinking in linguistic form).
The experiments in this chapter suggested (not explicitly and by Raschka's intention,
but by my own side association) that the "gestalt" part
could be enriched by dynamic addition of some context or insentive
(no idea yet how to do that technically though).

## Claude: On Activation Steering

Your notes read like someone who's read the book carefully. My reactions, checked against the chapter's code:

**1. "Logits can be analyzed, not only sampled from."** Yes, and there's a detail in how the book does it that's easy to miss. `avg_logprob_answer` doesn't score tokens while they're being generated. It scores a finished answer afterwards: it feeds prompt + answer through the model in one forward pass and averages the log-probability the model gives each answer token. So in the chapter, confidence is a judgment on a completed answer, used in one place: the accept/reject gate at the end of `self_refinement_loop` (`if revised_score >= current_score`). Your ideas go further than that, because you want to read these signals during generation and act on them. That's a real extension of the book, not a restatement of it.

**2. "Self-feeling" / self-reflection.** I'd frame it a little more carefully. The model doesn't look at its own probabilities. An outside procedure reads them. Also, confidence isn't correctness: a fluent, generic, or wrong-but-familiar answer can score high. The chapter has two separate mechanisms here:
- the **critique** step, where the model judges its draft *in text*
- the **log-prob score**, which is an external reading of the model's internal state

**3. Your investigation ideas map onto known territory:**
- **Turning points from logit sequences.** This is the easiest one to test with the chapter's code. `calc_next_token_logprobas` already gives per-token values, so you can plot per-token log-prob (or entropy) along a generated answer and see whether the dips line up with phrase or step boundaries. It also fits your presentation: small, visual, and it runs on CPU.
- **Re-branching from structural points at a different temperature, then merging.** This builds on Ch04's self-consistency. Ch04 branches from the start, and you'd branch mid-sequence. Outside the book, "entropy-triggered branching" and tree-search decoding are active research areas.
- **Deciding when to stop from the metrics.** This is the adaptive version of the chapter's fixed `iterations=2`.

**4. Gestalt vs. logic.** Your metaphor fits the chapter better than you might think. The log-prob score is a direct readout of the "gestalt" (the forward pass). The critique → refine loop is the "logic" side, and it works by putting text (the critique) back into the context, which changes the next forward pass. So the refine prompt is already a crude way of "dynamically adding context." The more direct technical version of what you're imagining is called **activation steering**: you add a vector to the hidden states mid-forward-pass, and the weights don't change. It isn't in this book, so treat it as a side read if it interests you.

**For the notebooks:** sections 5.4–5.6 (token probabilities → log-probs → answer confidence) are where your ideas plug in. When we get there, I can help you set up the per-token plot as a small experiment.

## Claude: Reading for Activation Steering

Here's a reading list on activation steering. I've ordered it so each item builds on the ones before. I put it together from memory and didn't look anything up, so if an arXiv link doesn't resolve, search for the title.

**The core idea: add a vector to the hidden states during inference**
1. **Subramani, Suresh & Peters (2022)**, *Extracting Latent Steering Vectors from Pretrained Language Models*, ACL Findings, [arXiv:2205.05124](https://arxiv.org/abs/2205.05124). An early paper showing that a single vector added to a hidden layer can steer what a frozen model generates.
2. **Turner et al. (2023)**, *Steering Language Models With Activation Engineering* (the "ActAdd" method), [arXiv:2308.10248](https://arxiv.org/abs/2308.10248). Start here. It takes the activation difference between two contrasting prompts (e.g. "Love" minus "Hate") and adds it in mid-forward-pass. It's short and readable.
3. **Rimsky (Panickssery) et al. (2024)**, *Steering Llama 2 via Contrastive Activation Addition*, ACL 2024, [arXiv:2312.06681](https://arxiv.org/abs/2312.06681). A more robust version of ActAdd: it averages the difference over many contrasting example pairs.

**Reading and steering "internal states" like truthfulness and confidence** (closest to your Ch05 ideas)
4. **Li et al. (2023)**, *Inference-Time Intervention: Eliciting Truthful Answers from a Language Model*, NeurIPS 2023, [arXiv:2306.03341](https://arxiv.org/abs/2306.03341). Finds attention heads that encode truthfulness and shifts them during generation. It's an inference-time improvement that leaves the weights untouched, the same spirit as Ch04–05.
5. **Zou et al. (2023)**, *Representation Engineering: A Top-Down Approach to AI Transparency*, [arXiv:2310.01405](https://arxiv.org/abs/2310.01405). Broader framing: first *read* concepts like honesty from the hidden states, then *control* them.
6. **Arditi et al. (2024)**, *Refusal in Language Models Is Mediated by a Single Direction*, [arXiv:2406.11717](https://arxiv.org/abs/2406.11717). A striking result: a single direction in activation space switches refusal on or off.

**Why this works at all: concepts are roughly linear directions**
7. **Park, Choe & Veitch (2023)**, *The Linear Representation Hypothesis and the Geometry of Large Language Models*, [arXiv:2311.03658](https://arxiv.org/abs/2311.03658).
8. **Anthropic, Templeton et al. (2024)**, *Scaling Monosemanticity*, [transformer-circuits.pub/2024/scaling-monosemanticity](https://transformer-circuits.pub/2024/scaling-monosemanticity/). Finds interpretable "features" with sparse autoencoders and steers with them. This is the "Golden Gate Claude" demo, where turning up one feature made the model bring up the Golden Gate Bridge constantly.
9. **Chen et al. (2025)**, *Persona Vectors*, [arXiv:2507.21509](https://arxiv.org/abs/2507.21509). Steers character traits, and can also monitor them.

**Hands-on**
- **Theia Vogel**'s blog post *Representation Engineering Mistral-7B an Acid Trip* (2024) and her library **`repeng`**. This is the friendliest practical introduction.
- With the book's own code, you can do it in a few lines: register a PyTorch `register_forward_hook` on one of `model.trf_blocks[i]` ([qwen3.py:37](reasoning_from_scratch/qwen3.py#L37)) and add a vector to its output. That's a natural "my own investigation" once you're through Ch05.

**For your branching idea:** search for **"entropix"** (entropy- and varentropy-based adaptive sampling, 2024). It branches or resamples when token-level uncertainty spikes. That's very close to what you described: finding turning points from the logit sequence and re-generating from there.

All of this is outside the book, so none of it spoils later chapters. Want me to save this list somewhere tracked, e.g. a "Side reading" section in `my-notes/Ch05.md`, so it reaches the ASUS machine?

## Me: Thinking Metaphor

Do humans think in words? The gestalt-vs-logic metaphire sades the light to that mechanism of thinking (even though in humans it is technically very differnt). The main point that the thinking must be at least the both: no good thinking is possible without massive patern matching (based on self-attention through many forward layets). However, the pattern matcnig is limited by its "declarative" nature. It works like a staic expression with no recurrence and limited conditional branching. Reasoning requires unlimited number of repetitive steps, and that's what autogeneration gives us. And that latter works through the language. So the logic works in words, insight works in paterns. This is of course just a metaphor, not a complete philosophy or technique. Just an image for explaining reasoning in LLMs.

We already discussed that in Chapter 04. I am just re-inforcing it here, since it appears to me as a very important observation. What do you think?

## Claude:  I think the core of your metaphor is right,
and there's theory behind it, not just intuition. I'd sharpen one word in it, though: what makes reasoning possible is the *loop*, and words are the channel that loop happens to run through in an LLM.

**What the theory says**

A single forward pass does a fixed amount of work: a fixed number of layers, no loops. Theory papers show that this puts real limits on what one pass can compute. Merrill & Sabharwal (*The Expressive Power of Transformers with Chain of Thought*, ICLR 2024) and Feng et al. (*Towards Revealing the Mystery behind Chain of Thought*, NeurIPS 2023) both prove that letting the model generate intermediate tokens strictly increases what it can compute. Roughly: more steps of thinking → harder problems become solvable. That's your "static expression vs. unlimited repetitive steps" point, stated formally.

**Why words are the loop in an LLM**

Within one token's forward pass, information moves strictly upward, layer 1 → layer N. Later tokens can attend to earlier tokens' hidden states (via the KV cache), so the model's earlier state isn't lost. But the only route from the *top* of the stack back to the *bottom* goes through the sampled token. So the sequence of tokens is literally the recurrence. "Logic works in words" is close to a description of how the system is built.

**Three caveats that make the image more interesting**

1. **The words may not be the actual reasoning.** Turpin et al. (2023, *Language Models Don't Always Say What They Think*) show chain-of-thought text can be a plausible story that doesn't match what actually drove the answer. The pattern-matching part did the work, and the words came after. Humans do this too: Nisbett & Wilson (1977) found people confidently report reasons for their choices that didn't actually cause them.
2. **Sometimes the words don't even need meaning.** Pfau et al. (2024, *Let's Think Dot by Dot*) found that meaningless filler tokens can help on some tasks, because each extra token buys another forward pass. Coconut (Hao et al., 2024) goes further: it feeds the hidden state back in place of a token, so the model reasons without words. Both suggest that language is the *channel* of the loop, not necessarily its *content*.
3. **Humans are the weaker case for the metaphor.** Fedorenko et al. (*Nature*, 2024, *Language is primarily a tool for communication rather than thought*) review evidence that people with severe aphasia can still do math, logic, and planning. Humans have non-verbal working memory (spatial, visual) that can carry the loop; inner speech is a helpful scaffold, not the only route. An LLM has no such alternative: tokens are its only loop. So your metaphor actually describes LLMs more accurately than it describes the human thinking it came from.

A tighter version of your line, if you want it for the talk: *"Insight is parallel pattern-matching in one pass; reasoning is iteration, and in an LLM the only way to iterate is to write something down."* It also connects Ch04 and Ch05 neatly. Chain-of-thought adds more iterations; self-refinement adds iterations over a whole answer (draft → critique → revise).

This could make a good slide, or a paragraph in `review/notes.md`. I'll leave it here unless you want me to put it somewhere.

## Me: Just one token?

Viewing the thinking through such a metaphor raises a question: why the "insight" produces just one word (token). Obviously, a pattern recognized by the model with thousands-token context window contains much more information than just one "next token". Technically we use just one because this is how our training process was organized. But if I think of it more generally, it seems like a huge loss for ignoring 99.99% of the insight just to re-compute it again and again in teh next iterations. And I am not concerned here about computational performance and optimization. It's just looks odd the way it is - by one token. I assume that this idea has been explored by LLM reserachers and there might be oher nice metaphors, techniques, etc. in response to such a question.

## Claude: Researchers have explored this a lot.
One part of the premise needs adjusting first, though, because it changes what the "loss" actually is.

**Not much of the insight is thrown away**

When the model produces a token, every layer's hidden state for every past position stays in the KV cache. The next forward pass attends to all of it, so it doesn't recompute the earlier insight; it rereads it. What does pass through the one-token bottleneck is only the feedback path from the top of the stack back to the bottom, which is the iteration loop from our last exchange. So the rich state is stored. What's narrow is the channel that carries a *decision* forward.

The hidden states also contain far more than the next token. Interpretability work shows models plan ahead:
- Anthropic's *On the Biology of a Large Language Model* (2025) shows Claude choosing a rhyme word before writing the line that leads up to it.
- Pal et al. (2023, *Future Lens*) decode several future tokens from a single hidden state.

So the "insight" includes a plan. The token is the part of that plan the model commits to.

**Why committing to one token can be a feature**

- **Collapsing ambiguity.** The model's distribution often holds several incompatible continuations at once. You can't write "both" of them, and averaging two plans gives nonsense. Sampling a token is a decision, and later steps build on a definite choice. A common metaphor here is superposition → measurement.
- **Error correction.** Rounding to a discrete symbol at each step stops small errors from piling up. It's like a digital signal versus an analog one, or why a clear spoken sentence is easier to build on than a vague feeling.
- **Training.** Next-token prediction lets the model train on every position of a text in parallel, with an exact target at each one. A large part of why the approach scaled is that it's simple.

**Approaches that take your question seriously**

These are from memory, so verify the details before you cite them:

| Idea | What it does | Key reference |
|---|---|---|
| **Multi-token prediction** | Predict several future tokens at once | Gloeckle et al. 2024, *Better & Faster LLMs via Multi-token Prediction* ([arXiv:2404.19737](https://arxiv.org/abs/2404.19737)); used in DeepSeek-V3 |
| **Continuous thought (Coconut)** | Feed the last hidden state back in place of a token, so the whole insight goes around the loop. The authors argue these thoughts can hold several reasoning paths at once (breadth-first search) | Hao et al. 2024, [arXiv:2412.06769](https://arxiv.org/abs/2412.06769) |
| **Soft thinking** | Feed back a probability-weighted mix of token embeddings, not one sampled token. This is very close to your Ch05 idea about using the full logits | Zhang et al. 2025, *Soft Thinking* |
| **Recurrent depth** | Loop a block of layers internally several times before emitting a token: more thinking per word | Geiping et al. 2025, [arXiv:2502.05171](https://arxiv.org/abs/2502.05171); earlier, Universal Transformers (Dehghani et al. 2018) |
| **Pause tokens** | Add "do-nothing" tokens that buy extra forward passes without committing to a word | Goyal et al. 2023, *Think Before You Speak* |
| **Concept-level models** | Predict whole-sentence embeddings, not tokens | Meta, *Large Concept Models* 2024 ([arXiv:2412.08821](https://arxiv.org/abs/2412.08821)) |
| **Diffusion LMs** | Draft the whole answer at once, then refine all positions in parallel over several steps | LLaDA (Nie et al. 2025); Gemini Diffusion, Mercury |

Diffusion LMs fit your metaphor best: the gestalt produces a whole draft in one go, and iteration refines it. That's structurally close to Ch05's draft → critique → refine loop, except it happens inside the model rather than through text.

**A line for your notes:** *"The model thinks in paragraphs but speaks in words. Speaking one word at a time isn't wasting the paragraph; it's the price of committing."* Coconut and soft thinking are attempts to drop that price, and they're early. So far, discrete tokens remain hard to beat for reasoning that has to be correct.

---
---
---
## Me: Another possible dimension of thinking 
Try to enrich the gestalt with extra information, such as goal, task, situation. I actually have no idea how to do so, just thinking that it might be moe efficient that simply adding such (maybe varying) "contex" to the prompt. So it;'s just a blind idea. A variation of that could be an attempt to add non-linguistic data to the context - maybe mix the text prompt with graphical scene, or music. Same: it's just a crazy thought. But I am sure you will point to existing ideas and research of that sort.

## Claude: Neither idea is crazy.
Both have active research behind them, and the second one is how today's multimodal models work. All references below are from memory, so check the details before citing them.

## 1. Feeding goal/task/situation in more directly than prompt text

There are roughly three levels where you can inject the extra information.

**Learned vectors in place of words** ("soft prompts")
- **Prompt tuning** (Lester et al. 2021, *The Power of Scale for Parameter-Efficient Prompt Tuning*) and **prefix tuning** (Li & Liang 2021). You train a few continuous vectors that sit in the context like tokens, but they aren't words. The model weights stay frozen. Prefix tuning inserts them at *every layer*, which is close to what you mean by "enriching the gestalt."
- **Gist tokens** (Mu et al. 2023, *Learning to Compress Prompts with Gist Tokens*). A long instruction gets compressed into a few vectors, which addresses your efficiency point directly.

**Direct edits to the hidden states**
- **Activation steering** from the earlier list: adding a "goal" or "persona" vector to the residual stream.
- **FiLM** (Perez et al. 2018) and **cross-attention conditioning**. The condition vector scales or shifts each layer, or the layers attend to it through a separate channel. Image diffusion models get their text prompt this way, and Flamingo-style models get their images this way.
- **Retrieval by cross-attention:** RETRO (Borgeaud et al. 2021) and Memorizing Transformers (Wu et al. 2022). The model attends to external memory without putting it into the prompt.

**Changes to the logits (this one ties into Ch05)**
- **Classifier-free guidance for LLMs** (Sanchez et al. 2023, *Stay on Topic with Classifier-Free Guidance*). Run the model twice, once with the goal context and once without, then combine the outputs: `logits = uncond + γ·(cond − uncond)`. A γ above 1 *amplifies* the goal's influence beyond what the prompt alone produces. The related idea is **contrastive decoding** (Li et al. 2022).

**A caveat on "more efficient than the prompt":** plain prompts are hard to beat. Every token in the context is visible to attention at every layer, so prompt text already reaches the "gestalt" fully. AxBench (Wu et al. 2025) found that ordinary prompting often outperformed representation steering at steering the model. Steering methods are cheaper and more precise, but they're usually not stronger.

## 2. Non-linguistic data in the context

This is how vision/audio LLMs are built. An encoder turns an image or audio clip into vectors. A small projection maps those vectors into the LLM's token-embedding space, and they're interleaved with the text as "soft tokens."

- **Frozen** (Tsimpoukelli et al. 2021). The LLM stays frozen; only the image encoder is trained, so it learns to emit a soft prompt. That joins your two ideas: an image used as a non-verbal soft prompt.
- **Merullo et al. 2022**, *Linearly Mapping from Image to Text Space*. A single linear layer is enough to make image features usable by a text-only LM. This suggests the LLM's latent space isn't really "linguistic"; it's general enough to take in other inputs.
- **Flamingo** (Alayrac et al. 2022) and **LLaVA** (Liu et al. 2023, *Visual Instruction Tuning*) are the standard designs.
- **Situation as input:** **PaLM-E** (Driess et al. 2023) feeds robot sensor states and camera images into an LLM. **RT-2** (2023) does the same and outputs robot actions.
- **Audio/music:** Qwen2-Audio and **Qwen2.5-Omni**, which handles text, image, audio, and video. These are from the same family as the book's Qwen3, so the architecture you're learning is the backbone.
- **Reasoning with images** (images used inside the chain of thought, as in OpenAI's o3, 2025) is still early research.

In terms of your metaphor: in these systems the gestalt is fed patterns directly, without going through words. The human parallel is Paivio's **dual coding theory**, which says people keep verbal and imagery representations side by side.

## A small experiment you could run with the book's code

Of everything above, classifier-free guidance is the easiest to try with what Ch05 gives you. You'd run two forward passes per step, one with and one without a goal line such as "Be concise" or "Double-check arithmetic", and mix the logits with γ = 1.5–3. It needs no training, it works with Qwen3-0.6B on CPU, and it's a direct test of whether amplifying the goal does more than stating it in the prompt. When you've got through the notebook's log-prob sections, I can help you build it.

## ME: Compute Cost
 I realize that most of these ideas probably require applying such "crazy" ideas during pre-training, for which I do not have sufficient computing resources. So one interesting question is: which of thos ideas could be explored on top of pretrained models - either in form of "inference scaling" on constant weights with just tricks around the fixed model, or in form of relatively cheaper fine-tuning. Pease give tell me something about it for my own future experiments.

 ## Claude: Your hunch is mostly right, 
 but the cutoff is lower than you might think. A lot of this works on top of a pretrained model, and with Qwen3-0.6B or 1.7B, even "fine-tuning" fits on one of your ASUS cards. I'd sort the ideas into three tiers.

## Tier A: weights frozen, inference tricks only (Surface Studio, CPU)

These all build directly on Ch04–05 code: the generation loop, `calc_next_token_logprobas`, and `avg_logprob_answer`.

| Experiment | What you'd build | Notes |
|---|---|---|
| **Per-token log-prob / entropy trace** | Plot entropy along a generated answer; check whether spikes line up with phrase or step boundaries | Your first Ch05 idea. Easiest starting point |
| **Entropy-triggered branching** | When entropy spikes, fork N continuations, possibly at a different temperature, and score them (avg log-prob or a heuristic) | Your branching idea; the entropix approach. A mid-sequence version of Ch04's self-consistency |
| **Adaptive stopping/iterations** | Decide whether to run another refinement round based on the confidence delta | Extends `self_refinement_loop`'s fixed `iterations=2` |
| **Classifier-free guidance** | Two forward passes per step (with and without a goal line), then `uncond + γ·(cond − uncond)` | Tests "amplify the goal beyond the prompt" |
| **Contrastive decoding** | Subtract a weaker model's logits from a stronger one's, e.g. Qwen3-0.6B from 1.7B | Needs two model sizes, still inference-only |
| **Activation steering (ActAdd)** | Collect hidden states for contrasting prompt pairs, take the mean difference, add it back with a forward hook on `model.trf_blocks[i]` | Needs no gradient training, only forward passes |
| **Soft thinking (training-free)** | Feed back a probability-weighted mix of token embeddings, not the single sampled token | The paper reports it working without training. Easy to code with the book's model, because you control the embedding step |
| **Logit lens** | Apply the final norm + output head to *intermediate* layers' hidden states to watch the prediction form layer by layer | Pure analysis, no steering. A good way to look inside the "gestalt" |

## Tier B: cheap training, small add-ons or light fine-tuning (ASUS, one GPU)

A rough sizing for your hardware: full fine-tuning in fp32 with Adam needs about 16 bytes per parameter (weights, gradients, and two optimizer states), before activations. For Qwen3-0.6B that's about 10 GB, and for 1.7B about 27 GB. Both fit on one 48 GB RTX 8000, so you don't need multiple GPUs (or gloo/NCCL) for this tier. Use fp16 or fp32, not bf16.

| Experiment | What gets trained | Cost / caveat |
|---|---|---|
| **Steering vectors, optimized** | One vector per layer, trained by gradient descent rather than simply averaged | Minutes. A step up from ActAdd |
| **Prompt / prefix tuning** | A few dozen soft-token vectors; the model stays frozen | Cheap. Caveat: Lester et al. found prompt tuning weak at small model scales, so expect modest results on 0.6B |
| **LoRA** | Low-rank adapters on the attention/MLP weights | Very cheap. The book's Qwen3 isn't a Hugging Face model, so `peft` won't plug in directly, but the companion *LLMs From Scratch* has LoRA from scratch in an appendix, and it ports easily |
| **Multi-token prediction heads** | Extra output heads on a frozen backbone that predict tokens t+2, t+3, … | Cheap (as in the Medusa-1 setup). Lets you test how much of "the future" the hidden state already holds |
| **Linear image → LLM projector** | One linear layer mapping frozen image-encoder features (e.g. CLIP/SigLIP) into Qwen3's embedding space, trained on image–caption pairs | A few GPU-hours, as in LLaVA's stage 1 and Merullo et al. The cheapest way to try your "non-linguistic context" idea |
| **Gist tokens** | Fine-tune (LoRA works) so the model compresses instructions into a few tokens | Moderate. Needs a dataset of instructions |
| **Coconut (continuous thought)** | Fine-tune with a curriculum that swaps chain-of-thought steps for fed-back hidden states | Moderate. The original paper used GPT-2-sized models, so 0.6B on your hardware is realistic |

## Tier C: mostly needs pretraining-scale compute, so skip or just read

- **Pause tokens:** the paper found gains mainly when they're added during pretraining; fine-tuning alone helped little.
- **Recurrent-depth models:** these are generally trained that way from the start.
- **Concept-level models:** these are new architectures, not add-ons to an existing model.
- **Diffusion LMs:** converting a pretrained autoregressive model is possible (Gong et al. 2024, *Scaling Diffusion Language Models via Adaptation from Autoregressive Models*), but it's a large project. Treat it as a stretch goal at most.

## A suggested order

1. **Entropy trace → entropy-triggered branching**, on the Surface, right after notebook sections 5.4–5.6. Your own idea, the book's code, cheap.
2. **CFG and ActAdd steering:** two short experiments on the "goal enrichment" idea.
3. **Logit lens** whenever you want to look inside a single forward pass.
4. On the ASUS: **MTP heads** or the **image projector**, your first real training experiment, and well within one card.

A note on what's coming: Chapters 6–8 are themselves about training a pretrained model further, which fits your Tier B. I won't go into how they do it. Once you've read them, they'll probably change which Tier B items look most interesting.

Should I save this as a tracked roadmap, e.g. `my-notes/experiment-ideas.md`, together with the earlier reading lists? That way it reaches the ASUS machine and won't get lost in this thread.
