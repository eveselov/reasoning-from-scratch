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

