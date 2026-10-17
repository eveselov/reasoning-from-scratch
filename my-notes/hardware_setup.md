**Q: I realized that I am plugging my 4 gpu ASUS into a normal home power outlet, which seems to be dangerous. To avoid troubles I removed three of GPS and how have only one left in the computer. Three other will be witing for the future when I add a more capable circuit. Do you think it was reasonable?**


Yes, it was reasonable, and on the cautious side. Your worry was valid, but only for the case where all four cards run flat out for a long time. With one card the machine fits comfortably on an ordinary outlet.

I'm assuming a standard US home circuit (120 V, 15 A), since the ASUS's timezone is set to US Pacific.

**Why four cards was a real concern:**
- Each Quadro RTX 8000 is limited to 260 W, so four cards at full load draw about 1,040 W.
- The Xeon W-2195 adds about 140 W, and the rest of the system roughly another 100 W.
- That's about 1.3 kW inside the machine, or about 1.4 kW from the wall once power-supply losses are counted.
- A 15 A circuit is rated for about 1,440 W of continuous load (80% of 1,800 W). Four cards under sustained training load sit right at that limit, before counting anything else on the same circuit.
- The breaker would normally trip before anything dangerous happens. The real hazards are a worn outlet, a cheap power strip, or an extension cord heating up during hours of near-maximum draw.
- At idle (the remaining card is drawing 8 W right now) or during short runs, four cards were never a problem.

**With one card:** peak draw is roughly 500–550 W at the wall, which is no concern on any normal outlet.

**For the book, one card is enough:** 48 GB of GPU memory is plenty for the small model the book uses, and Windows can't do fast multi-GPU training anyway, as your CLAUDE.md notes.

**An alternative for later:** you could put the cards back and cap their power with `nvidia-smi -pl 150` (needs admin; this card accepts 100–260 W). Four cards at 150 W would draw about 600 W, which keeps all 192 GB of GPU memory at the cost of some speed. Physically removing them is still the simpler and more foolproof choice until you have a dedicated circuit.

**Current state:** I checked, and the remaining card is GPU 0 in WDDM mode at 26 °C. NVLink shows no active links, as expected with its partner gone.

**Q: Before you apply the edits, tell me what happens if I try to go beyond the book's requirements. For instance, can I download a Qwen3 model with bigger requirements and run it instead of what's in the book? How that would affect GPU requirements. I want to start making such experiments earlier, so maybe I need to re-install the gpus back...**

Yes, you can swap in a bigger Qwen3 model. The book's code already includes the settings for larger sizes, and one 48 GB card covers more than you might expect. You don't need to reinstall anything to start experimenting.

**The code already supports it.** [reasoning_from_scratch/appendix_c.py](reasoning_from_scratch/appendix_c.py) has ready-made configurations for Qwen3 1.7B, 4B, 8B, 14B and 32B, plus a function that loads the official Hugging Face weights into the book's model class. The book also has an appendix on exactly this question: **Appendix D, "Using Larger LLMs"** ([chD/chD_main.ipynb](chD/chD_main.ipynb)). Reading it before you experiment wouldn't spoil the main chapters. I haven't looked inside it, to respect your follow-the-book rule.

## Running a model (Chapters 2–5)

Memory is mostly the model's weights: 2 bytes per parameter at 16-bit precision, 4 bytes at 32-bit.

| Model | 16-bit | 32-bit | One 48 GB card? |
|---|---|---|---|
| 0.6B (book) | 1.2 GB | 2.4 GB | trivially |
| 1.7B | 3.4 GB | 7 GB | yes |
| 4B | 8 GB | 16 GB | yes |
| 8B | 16 GB | 32 GB | yes, even at 32-bit |
| 14B | 28 GB | 56 GB | only at 16-bit |
| 32B | 64 GB | 128 GB | **no**: needs 2 cards, or compression to 8-bit |

Add some headroom for the memory used while generating. For an 8B model that's about 0.15 MB per token, so a few GB even when sampling many answers at once, as Chapter 4's techniques do.

**A catch specific to this card (Turing):** the configurations use bfloat16, a 16-bit format this card has no hardware support for, which is why your CLAUDE.md says to prefer fp16/fp32.
- My understanding is that PyTorch still runs bfloat16 on this card by emulating it in software, which is slower. I haven't tested it on your machine.
- Switching to fp16 is risky: Qwen models are known to produce intermediate values too large for fp16, which shows up as garbage text or NaNs.
- Running at fp32 is the safe choice and still fits 8B on one card.

**Speed:** generating one token means reading every weight once, and this card reads about 670 GB/s. That puts a ceiling of roughly 40 tokens/s on an 8B model at 16-bit, or about 20 at 32-bit. The book's plain PyTorch code will be slower than that. A Chapter 4-style evaluation over hundreds of math problems, sampling each several times, becomes hours instead of minutes.

## Training (Chapters 6–8)

Full fine-tuning needs roughly 16 bytes per parameter (weights, gradients and optimizer state), plus working memory. RL training (GRPO) also generates many sample answers and keeps a copy of the original model for comparison.
- **One card:** 0.6B is comfortable, 1.7B is probably feasible, 4B and up is not, unless you train only small adapter layers (LoRA) instead of the full model.
- **Several cards:** they help only if the training code spreads the model across GPUs, and that is slow on Windows. You would likely need WSL2, as your CLAUDE.md already notes.

## Do you need to reinstall the cards?

- **Up to 8B, and 14B at 16-bit:** no, one card is enough.
- **For 32B or bigger training runs:** reinstall just one card, the NVLink partner of the remaining one, with its bridge.
  - Two cards draw about 2 × 260 + 140 + 100 ≈ 760 W inside the machine, roughly 850 W from the wall, which is well within a 15 A home circuit.
  - When a model is split across two cards for generation, the cards take turns, so the actual draw is lower still.
- **All four** stays the case that needs either a dedicated circuit or power caps (`nvidia-smi -pl 150`).

**Q: Tell me more about "nvidia-smi -pl 150" command. And explain the differences between bfloat16, fp16, fp32, and overall anbout "Turing" system.**

## `nvidia-smi -pl 150`

`-pl` is short for `--power-limit`. It sets a cap in watts that the card's own power management enforces by lowering its clock speed and voltage whenever it would draw more.

- **Range:** it only accepts values the card allows. Yours reports 100 W minimum and 260 W maximum, which is also the default.
- **Needs admin:** run it from an administrator PowerShell.
- **Which cards:** without `-i` it applies to every GPU. `nvidia-smi -i 0 -pl 150` sets only GPU 0.
- **Doesn't survive a reboot:** on Windows the setting resets to the default after a restart or driver reload. To make it permanent, run it from a Task Scheduler task at startup with highest privileges.
- **Check it:** `nvidia-smi --query-gpu=index,power.draw,power.limit --format=csv`, or `nvidia-smi -q -d POWER` for the full detail.
- **Cost in speed:** smaller than the cut in power, because the last watts buy the least performance. A card capped near 60% typically keeps most of its throughput on heavy compute. Text generation is mostly limited by memory speed rather than compute, so it loses even less. I haven't measured this on your card; a capped-versus-uncapped run of the benchmark below would tell you.
- **Limits:** it caps the average power. Very short spikes can briefly exceed it, which doesn't matter for a circuit breaker, since breakers respond to sustained load.

## fp32, fp16, bfloat16

All three store a number as a sign, an exponent (which sets the **range**, how big or small a number can be) and a mantissa (which sets the **precision**, how many significant digits).

| Format | Bits (sign / exponent / mantissa) | Largest value | Smallest normal value | Significant digits |
|---|---|---|---|---|
| fp32 | 1 / 8 / 23 | ~3.4×10³⁸ | ~1.2×10⁻³⁸ | ~7 |
| fp16 | 1 / 5 / 10 | **65,504** | ~6×10⁻⁵ | ~3 |
| bfloat16 | 1 / **8** / 7 | ~3.4×10³⁸ | ~1.2×10⁻³⁸ | ~2–3 |

- **fp32** ("single precision") is the traditional default: accurate and wide-ranging, but 4 bytes per number.
- **fp16** ("half precision") halves the memory, but its range is tiny. Anything above 65,504 becomes infinity, and very small numbers round to zero.
- **bfloat16** ("brain float", from Google Brain) keeps fp32's 8 exponent bits, so it has the same range, and gives up precision instead. It is just fp32 with the low 16 bits cut off.

Neural networks tolerate imprecision well but break when values overflow, which is why bfloat16 became the standard for modern LLMs. Qwen3 was trained in it, and the book's configurations use it.

Your card shows the difference directly. Converting `[70000, 1e-8, 1.0001]`:

```
fp32  -> [70000.0,  1e-08,    1.0001]
fp16  -> [inf,      0.0,      1.0   ]   <- overflow and underflow
bf16  -> [70144.0,  1.0e-08,  1.0   ]   <- right range, rough digits
```

That `inf` is why fp16 is risky for Qwen: some of its intermediate values are large enough to overflow, and from there the output turns into NaNs or garbage. Training in fp16 also needs a workaround called loss scaling to keep small gradient values from rounding to zero; bfloat16 doesn't need it.

## "Turing"

Turing isn't the whole system but NVIDIA's name for a GPU architecture generation, the chip design shared by every card from about 2018: the RTX 20-series, the Quadro RTX line including yours, and the T4. PyTorch calls it compute capability 7.5, or `sm_75`.

| Generation | Year | Notable for ML |
|---|---|---|
| Volta | 2017 | first tensor cores (fp16) |
| **Turing** | 2018 | 2nd-gen tensor cores: fp16, int8, int4 |
| Ampere | 2020 | **bfloat16** and TF32 in hardware, FlashAttention 2 |
| Ada / Hopper | 2022 | fp8 |
| Blackwell | 2024 | fp4 |

Tensor cores are specialised matrix-multiply units, many times faster than the general-purpose cores. On Turing they handle fp16 but not bfloat16. Here are the same 8192×8192 matrix multiplications measured on your card:

```
fp32 :  13.9 TFLOPS   general-purpose cores
fp16 :  92.9 TFLOPS   tensor cores (6.7x fp32)
bf16 :   7.9 TFLOPS   software-emulated: slower than fp32
```

So PyTorch reports bfloat16 as "supported" on this card, but only through emulation (`is_bf16_supported(including_emulation=False)` returns `False`), and it ends up slower than fp32.

This benchmark measures pure compute. Generating text one token at a time is mostly limited by how fast weights can be read from memory, so the real gap there will be smaller, and bfloat16 at least halves the bytes read compared with fp32. I haven't measured that case.

What this means in practice on your card:
- **Default to fp32.** It is safe and not slow, and an 8B model still fits on one card.
- **Use fp16** when you need the speed or memory and can watch for `inf`/NaN outputs.
- **bfloat16** runs fine, just slowly; nothing breaks if the book's code uses it.
- **FlashAttention 2** is missing too, since it needs Ampere or newer. PyTorch falls back to another attention method, so this costs speed but nothing else.

For context, this card was built for 3D rendering and 2018-era deep learning. Its 48 GB of memory is still very generous; its compute formats are a generation behind current LLM practice.

The CLAUDE.md edit is still waiting on your go-ahead. I can also add a short line there about the fp32 default and the fp16 overflow risk if you'd like that recorded.

### Current Sutup

I've updated the GPU machine section of [CLAUDE.md](CLAUDE.md):

- **Current setup:** it now describes the single Quadro RTX 8000 in WDDM mode, why the other three came out on 2026-10-17, and that two cards (about 850 W) are fine on a home circuit.
- **GPU choice:** `cuda:0` is the only GPU. For two GPUs later, use an NVLink pair: `0,1` or `2,3`.
- **New "Switching back to 4 GPUs later" note:**
  - Only do it once you have a dedicated circuit, or with each card capped at `nvidia-smi -pl 150`. The cap needs admin and resets on reboot, so it should run from a scheduled task at startup.
  - Reinstall the NVLink bridges for pairs 0↔1 and 2↔3.
  - Restore the old driver modes with `nvidia-smi -i N -dm 1` (TCC) or `-dm 0` (WDDM): GPUs 0–2 in TCC, GPU 3 in WDDM to draw the remote desktop. This needs admin and a reboot.
