# Building Instructions for Reasoning From Scratch on GPU

## Question to Claude

This is a repository from Sebastian Raschka's new book "Build a Reasoninng Model From Scratch".

I created a fork of his repository and this is its local clone on one of my CPU machines. I also have a pretty powerful GPU server - ASUS with 4 RTX 8000 GPUs.

My ultimate goal for this project is to go through the entire book line by line, reproduce all the experiments and exercises and prepare a short cycle of lectures for my narrow group of friends about this topic - pretty much following the book's narrative. Lats time I did that for Sebastian's book "Build LLM from scratch"; now I want to repeat that in a form of a series of jupyther noteooks - one per lecture. I am expecting something between 3 to 6 lectures. My audience is a set of my friends - former Microsoft colleguaues with deep and not so deep knowledge of AI - as an "popular" overview of the technology.

I haven't yet started working with the book and have no particular plan of lectures - I will come for your help later. For now, as my first step I want to establish a working environment between my desktop Surface Studio (CPU machine) and ASUS server with Windows 11 (GPU machine). I want to work on ASUS server from the Surface Studio machine as a terminal. Please give me general recommendations of how to organize my work and how to estanlist remote connection between Surface Studio and ASUS server. I intend to use Remote SSH connection.

## Claude's Recommendation

Here's a practical setup plan, tailored to what's actually in pyproject.toml (this project uses uv, targets Python 3.10–3.14, and pulls in Torch 2.10+, JupyterLab, plus optional extras for later chapters like transformers, datasets, chainlit).

### 1. Overall shape of the workflow

Treat the Surface Studio purely as a thin client: an editor/terminal front-end. All code, the git checkout, the Python env, and Jupyter itself live on the ASUS box, which has the GPUs. You never want to be scp'ing checkpoints or datasets back and forth — everything runs where the RTX 8000s are, and you just look at it remotely.

Two ways to "look at it":

- **VS Code Remote-SSH** — window opens as if local, but the whole workspace/extension host runs on ASUS. Best for editing code, running notebooks in-editor, debugging.
- **Plain terminal SSH** — for quick commands, git, nvidia-smi, launching long training runs (ideally inside tmux/Windows Terminal + a persistent session so a dropped connection doesn't kill a run).

For notebooks specifically, you have two reasonable options — worth deciding once you're closer to actually running things:

- Open .ipynb files directly in VS Code (Remote-SSH window) with the Jupyter extension, kernel = ASUS's Python env. Simplest, no extra ports to manage.
- Run jupyter lab on ASUS and reach it via SSH port-forwarding to a browser on the Surface. Nicer for the "lecture demo" feel (bigger browser real estate, output slides), but one more moving part.

I'd start with the VS Code route since it reuses the SSH tunnel you're setting up anyway; add Lab later if you want it for the actual lecture presentation.

### 2. SSH: ASUS server side (Windows 11)

Windows 11 ships OpenSSH Server as an optional feature — no third-party tool needed.

On the ASUS server, in an elevated PowerShell:

```
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

A couple of Windows-specific gotchas worth knowing up front:

- Default shell for SSH sessions is cmd.exe. Switch it to PowerShell (or leave it, and just launch pwsh/powershell yourself) via:
```
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\PowerShell\7\pwsh.exe" -PropertyType String -Force
```
- If ASUS ever sleeps/hibernates, SSH obviously can't reach it — disable sleep for that machine (powercfg /change standby-timeout-ac 0) since it's meant to be always-on.
- Give it a stable local IP (DHCP reservation on your router, or a static IP) so you're not hunting for its address every session.

### 3. SSH: key-based auth (do this, skip passwords)

From the Surface Studio:

```
ssh-keygen -t ed25519 -C "surface-studio"
```
Then get the public key onto ASUS. Windows OpenSSH is picky here — for an administrator account the key file is different from a normal user:

- Normal user: append to C:\Users\<you>\.ssh\authorized_keys on ASUS.
- Admin user: must go into C:\ProgramData\ssh\administrators_authorized_keys, and that file needs ACLs restricted to Administrators/SYSTEM only (icacls — the sshd service refuses to use it otherwise). Easiest path: create/use a non-admin local account on ASUS just for this remote-dev work, so you land in the normal ~/.ssh/authorized_keys path.

Then set up an SSH config entry on Surface (~/.ssh/config — C:\Users\<you>\.ssh\config on Windows):

```
Host asus-gpu
    HostName 192.168.x.x
    User <asus-username>
    IdentityFile ~/.ssh/id_ed25519
```
That single alias (ssh asus-gpu) is also what VS Code's Remote-SSH extension will pick up automatically for the host picker.

### 4. Reachability: LAN vs. remote

If both machines are always on the same home/office network, plain LAN SSH is enough — nothing further to do. If you'll ever want to reach ASUS from outside that network (say, prepping a lecture from elsewhere), don't port-forward 22 on your router — put both machines on a Tailscale tailnet instead (free for personal use, WireGuard-based, zero-config NAT traversal). Then your SSH config's HostName becomes the stable Tailscale IP/MagicDNS name and works identically on-LAN or off. Worth setting up now even if you don't need it yet — five minutes, and it removes "which network am I on" as a variable later.

### 5. VS Code Remote-SSH

On the Surface: install the Remote - SSH extension, Ctrl+Shift+P → "Remote-SSH: Connect to Host" → asus-gpu. First connection installs a VS Code server on ASUS automatically (needs outbound internet from ASUS once). After that, open the repo folder remotely and install the Python + Jupyter extensions — they get installed into the remote extension host, separate from your local ones.

### 6. Python environment on ASUS

The repo already standardizes on uv (see uv.lock and the [tool.uv] block in pyproject.toml). On ASUS:

```
irm https://astral.sh/uv/install.ps1 | iex   # if uv isn't installed yet
git clone <your-fork-url> reasoning-from-scratch
cd reasoning-from-scratch
uv sync --extra extra --group dev
```

One thing to check explicitly once you're there: pyproject.toml only pins a CUDA-specific Torch index for linux+aarch64 (pyproject.toml:80-87); on Windows, uv sync will pull whatever the default torch>=2.10 wheel resolves to from PyPI, and you need to confirm it's actually the CUDA build, not CPU-only. Verify with:

```
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

If cuda.is_available() is False, you'll need to force an explicit CUDA-enabled index (uv add torch --index https://download.pytorch.org/whl/cu126 or similar, matched to ASUS's installed NVIDIA driver). Also worth an early nvidia-smi on ASUS to confirm all 4 RTX 8000s and the driver version. Two RTX 8000-specific notes for later in the book: they're Turing (48GB VRAM each, great for large batches/KV caches, no flash-attn-style SDPA acceleration on older kernels, and no native bf16 tensor-core support — the book examples using bfloat16 for training stability may need fp16 or fp32 fallback on this hardware; watch for that when you get to the training chapters).

### 7. Git flow between fork and clone
Standard triangle: origin = your fork, add upstream = Sebastian's repo so you can pull in book updates:

```
git remote add upstream https://github.com/rasbt/reasoning-from-scratch.git
```

Since ASUS is where you'll actually run and edit things, that's likely where you want your working branches; treat the Surface-side clone (if you keep one) as read-only reference, or don't bother cloning locally on Surface at all — the Remote-SSH window already gives you a full editing experience against the ASUS checkout.

### 8. Lecture-notebook organization (for later)

Not urgent now, but since you mentioned the "Build LLM from Scratch" precedent: consider a top-level lectures/ directory (outside ch01…chG, or in your fork only) with one notebook per lecture, each importing/reusing functions from reasoning_from_scratch rather than duplicating book code — keeps lecture notebooks focused on narrative + visuals rather than reimplementation. We can design the actual chapter→lecture mapping once you've started reading and know the book's pacing.

---

Once SSH is up, a good first checkpoint is: ssh asus-gpu "nvidia-smi" from the Surface terminal, then open the repo in a VS Code Remote-SSH window and run uv sync + the CUDA check above. Ping me when you hit that point (or if uv sync / driver issues come up) and I can help debug directly.

# ASUS Machine Configuration (inspected by Claude)

This ASUS box is in excellent hardware shape. The main problem is that PyTorch in the project's .venv can't use any of the GPUs.

### What's in the machine
GPUs	4 × NVIDIA Quadro RTX 8000, 48 GB each (192 GB total), Turing architecture (sm_75)
NVLink	Two pairs: GPU 0↔1 and GPU 2↔3. Each pair uses 2 links at about 25.8 GB/s each. There's no NVLink between the pairs; that traffic goes over PCIe.
Driver	582.16, supports CUDA up to 13.0
Driver mode	GPUs 0–2 run in TCC (compute-only, the best mode for training). GPU 3 runs in WDDM and drives the desktop, which is already using 2.7 GB of it.
CPU / RAM / disk	Xeon W-2195 (18 cores / 36 threads), 256 GB RAM, 3.5 TB free on C:
Condition: all 4 GPUs look healthy. They idle at 24–33 °C, all fans are working, there are no thermal or hardware slowdowns, no retired memory pages, and all run at the full 260 W power limit. The PCIe link shows Gen1 on three cards only because they're idle and saving power. All four run at x16 and can reach Gen3 under load.

### Adjustments I recommend

1. **Install a CUDA build of PyTorch (this blocks all GPU work).**
The .venv has torch 2.10.0+cpu, so torch.cuda.is_available() is False. Your BUILD.md predicted this. In pyproject.toml:80-82, the CUDA package index is only used on Linux ARM64, so uv sync on Windows installs the CPU version from PyPI. The durable fix is to add a Windows rule under [tool.uv.sources]:

```
torch = [
    { index = "pytorch-cu130", marker = "sys_platform == 'linux' and platform_machine == 'aarch64'" },
    { index = "pytorch-cu128", marker = "sys_platform == 'win32'" },
]
```
You'd also add a matching [[tool.uv.index]] entry for https://download.pytorch.org/whl/cu128, then run uv sync. I'd pick cu128 because it definitely supports Turing (sm_75) and works with your driver. This changes an upstream file, so expect a small merge conflict if Raschka edits that block later. I can make the change and check that PyTorch sees all 4 GPUs if you'd like.

2. **Stop the machine sleeping during long runs.** It's set to sleep after 60 minutes on AC power, which would kill a training run. Fix with powercfg /change standby-timeout-ac 0 (admin), and optionally switch the power plan to High performance.

3. **Remote access isn't set up yet.** The OpenSSH server (sshd) isn't installed on this machine. Section 2 of BUILD.md has the commands to install it.

4. **Keep heavy jobs off GPU 3 when you can.** It's the display GPU, so the desktop uses some of its memory and its runs can be slightly jittery. For a 2-GPU job, use an NVLink pair (CUDA_VISIBLE_DEVICES=0,1). Don't move the display to another card; this layout is fine.

**Limits to know about (no change needed now):**

- **bfloat16:** Turing has no native bf16 support, so bf16 code runs emulated and slowly. Use fp16 or fp32 on this hardware.
- **Multi-GPU on Windows:** Windows PyTorch has no NCCL, the usual fast library for moving data between GPUs. Multi-GPU training falls back to the slower gloo backend. If a later chapter needs serious multi-GPU training, WSL2 (Linux on Windows, not installed yet) would give you NCCL. That's a decision for later; I'm not looking ahead in the book.
- **ECC** (error-correcting memory) is off. Leaving it off is fine for this project.

The notable finding for your notes is that this box is the 4-GPU machine but its environment is still CPU-only. Once PyTorch sees the GPUs, I'll propose a CLAUDE.md edit covering that and the hardware facts above (you'd see the diff before I apply it).

### Q: I use this machine normally without display - via remote desktop conncetion. How does this afect your recommendation about heavy jobs off GPU 3? Can I just ignore it?

Mostly yes, you can ignore it. Running headless over RDP changes the reason for the recommendation, though, not whether GPU 3 carries a desktop load.

**GPU 3 still carries your desktop load.** On Windows 11, a Remote Desktop session is drawn on a hardware GPU by default, and GPU 3 is the only one in WDDM mode (the only mode that can render graphics). The process list I pulled earlier shows this: Explorer, Edge, VS Code, OneDrive and Windows Terminal all sit on GPU 3, using 2.7 GB. It's your RDP session's graphics, not a physical monitor.

**Why it hardly matters:**

- 2.7 GB is about 5% of 48 GB, so memory is not a real constraint.
- The speed cost of WDDM versus TCC mode is small (slightly slower kernel launches plus a little competition from desktop rendering). You'd notice it only when timing runs closely across GPUs.
- PyTorch uses cuda:0 by default, and GPU 0 is in TCC mode. Single-GPU notebooks will never touch GPU 3 unless you ask for it.

**One real, if unlikely, risk:** WDDM GPUs have a Windows watchdog (TDR, Timeout Detection and Recovery). If a single GPU operation runs longer than about 2 seconds, Windows resets the driver and your job crashes. Normal PyTorch operations are far shorter, so this is unlikely. If you ever see a "display driver stopped responding" crash during a run on GPU 3, this is why.

**Practical rule:**

- For single-GPU work, do nothing; the default GPU 0 is correct.
- For a 2-GPU job, use 0,1 (they're also linked by NVLink).
- For a 4-GPU job, use all four and accept that GPU 3 is slightly slower.

**Once SSH is set up, this matters even less.** With VS Code Remote-SSH from the Surface, the editor window runs on the Surface. Only the Python processes run on the ASUS, so they don't create desktop graphics on GPU 3. Its load would mostly disappear whenever you're not also logged in over RDP.

**Don't switch GPU 3 to TCC mode as well.** *RDP would still work with software rendering, but if RDP ever breaks, you'd have no GPU that can drive a display for fixing things locally. The Xeon W-2195 has no built-in graphics to fall back on. Very little performance is at stake, so it isn't worth that risk.*