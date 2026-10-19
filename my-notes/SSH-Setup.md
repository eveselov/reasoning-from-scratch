# HSS Setup

All four GPUs work. The newly started pair passed every test, and the heaviest load I ran drew 650 W across the four cards. Two things remain: the new pair's NVLink connection is inactive, and the power cap isn't set yet.

## Test results (PCI bus order, same numbering as `nvidia-smi`)

| GPU | Bus | Mode | Correctness | ~44 GiB memory test | Full load, 40 s |
|---|---|---|---|---|---|
| 0 | 0x19 | WDDM (now drawing the desktop) | OK | OK | 89 TFLOPS, peaked at 62 °C |
| 1 | 0x1A | WDDM | OK | OK | 89 TFLOPS, peaked at 73 °C |
| 2 | 0x67 | TCC | OK | OK | passed earlier |
| 3 | 0x68 | TCC | OK | OK | passed earlier |

**Power:** the peak while testing was **650 W** for all four cards (GPUs 0 and 1 at about 260 W each, GPUs 2 and 3 at about 65 W from the copy test). Idle is about 60 W in total. I never loaded more than two cards at once.

**NVLink:**
- GPUs 2↔3: active, 43.7 GiB/s.
- GPUs 0↔1: **inactive**, with only 9.3 GiB/s going over PCIe.
- The likely reason is that GPUs 0 and 1 are in WDDM mode. On Windows, direct card-to-card transfers (and in practice NVLink) need TCC mode. The 2↔3 pair is in TCC and works.
- A badly seated bridge is the other possibility. Switching both cards to TCC will tell us which.

**Why the cards failed at boot:** the plugs were fine, since the cards started as soon as the driver was asked again. The driver failed to start them during boot, possibly connected to their WDDM mode, but I haven't confirmed that. It may happen again on the next reboot.

## Steps for you, from an administrator PowerShell

**1. Switch GPUs 0 and 1 to TCC, then reboot.** This should activate their NVLink and may also stop the boot-time failure.

```powershell
nvidia-smi -i 0 -dm 1
nvidia-smi -i 1 -dm 1
```

After this, no GPU draws the desktop, and remote desktop falls back to Microsoft's software display adapter. That's how this session ran earlier today, and it worked fine. If you'd rather keep a GPU for the desktop, leave GPU 0 in WDDM, but that pair's NVLink will probably stay off.

**2. Cap all four at 150 W automatically at every boot.** Run this before running all four cards together:

```powershell
schtasks /create /tn "GPU power cap 150W" /tr "C:\Windows\system32\nvidia-smi.exe -pl 150" /sc onstart /ru SYSTEM /rl HIGHEST
schtasks /run /tn "GPU power cap 150W"
```

That limits the four cards to a combined 600 W, which I estimate at about 800 W from the wall. Without the cap, all four together would total about 1.4 kW, which is at the limit of your home circuit.

**3. If GPUs 0 and 1 show Code 43 again after a reboot**, rerun the two `pnputil /restart-device` commands from before. If it keeps happening, I can set that up as a startup task too.

GPU 1 runs about 10 °C hotter than its neighbours, both at idle and under load, probably because of where it sits in the airflow. Keep an eye on it during long runs; the 150 W cap will also help.

After the reboot, ask me and I'll verify all four (TCC mode, both NVLink pairs, 150 W caps) and run a capped test on all four together. Once that passes, I'll propose the CLAUDE.md hardware update for the four-card layout.

# Q: I wonder, if I switch all four cards to TCC will I loose the video? I do not have any display connected to ASUS, using it via remote desctop from my Surface Studio. Will nmy SUrface Studio display give me normal access to ASUS with all four GPUs in TCC mode?

Yes, remote desktop will keep working normally with all four cards in TCC. You're already running that way: after this evening's 19:48 reboot both visible cards were in TCC, and this session worked fine, including all the tests.

## How it works
- A remote desktop session never uses the GPU's video outputs. Windows draws your session onto a virtual screen, the **Microsoft Remote Display Adapter** (it showed up in the device list earlier), and streams it to the Surface.
- With a WDDM card present, Windows uses that GPU to draw the desktop faster. That's why GPU 0 now lists `explorer.exe`, `dwm.exe` and so on.
- With every card in TCC, Windows draws the desktop on the CPU instead. With 18 Xeon cores that costs a little CPU and is barely noticeable.

## Small trade-offs
- **Graphics-heavy apps** fall back to software drawing, a little more slowly. That includes VS Code's interface and browsers; I'd expect it to be barely noticeable.
- **Video compression for the stream:** your remote desktop log showed `AVC available: 0`, so the stream wasn't using hardware video compression anyway. You lose nothing there.
- **No local console:** a monitor plugged into any of the cards would go dark once Windows loads the NVIDIA driver. Since you don't use one, that only matters for rescue (below).
- **GPU memory:** on the plus side, all 4×48 GB is free for your models. In WDDM mode the desktop was using about 665 MiB on GPU 0.

## Safety net, in case remote desktop ever breaks
1. **SSH** is still an open item in your CLAUDE.md, with steps in [BUILD.md](BUILD.md) §2. Setting it up gives you a second way in that doesn't depend on remote desktop or graphics, so it's worth doing before or alongside the TCC switch.
2. **A monitor plus Safe Mode:** the BIOS and boot screens still appear on a card's output before Windows loads the NVIDIA driver. Safe Mode doesn't load that driver, so the desktop shows on a plugged-in monitor there too. From Safe Mode you can switch a card back with `nvidia-smi -i 0 -dm 0` and reboot. (I'm fairly confident about the Safe Mode behaviour but haven't tested it on this machine.)

Going all-TCC is the setup I'd recommend: it should activate the 0↔1 NVLink and frees all GPU memory, and you keep normal remote desktop access.


You set SSH up once and never need to rerun it, after sleep or after a reboot. But don't run the BUILD.md shell-switch line as written yet: it points to PowerShell 7, which isn't installed on the ASUS.

## Re-running after sleep or reboot

Every line in §2 makes a permanent change:

| Command | What it does | Survives sleep / reboot |
|---|---|---|
| `Add-WindowsCapability … OpenSSH.Server` | Installs the SSH server | yes, installed for good |
| `Start-Service sshd` | Starts it now, this one time | not needed again (see next line) |
| `Set-Service sshd -StartupType Automatic` | Starts it automatically **at every boot** | yes |
| `New-NetFirewallRule … 22` | Opens port 22 | yes |
| `New-ItemProperty … DefaultShell` | Sets the default shell | yes, it's in the registry |

**Sleep and wake:** sleep freezes the whole machine as it is, including the running SSH server. When you press the front button, it carries on and is ready within seconds. Just connect again.
- An SSH or VS Code Remote-SSH connection that was open when the machine went to sleep will be dropped. Reconnect (VS Code shows a "Reconnect" button).
- Anything you had started inside that SSH session is usually ended along with it. So don't put the machine to sleep in the middle of a run.

## cmd.exe vs. PowerShell
**Switching is optional.** It only decides which shell you land in when you type `ssh asus-gpu`:
- **cmd.exe (the default):** old-style commands, so PowerShell commands like `Get-Process` won't work directly. You can always type `powershell` to switch inside the session.
- **PowerShell:** the same shell you use everywhere else on these machines, so commands from the book's Windows notes, from me, and from your own habits work as-is.
- **VS Code Remote-SSH** works with either.

**Don't run that line as written.** It points to `C:\Program Files\PowerShell\7\pwsh.exe`, which is **not installed** on the ASUS (I checked). SSH would then try to start a program that doesn't exist, and every login would fail. Pick one of these:

```powershell
# Option A: use the Windows PowerShell 5.1 that's already there
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force

# Option B: install PowerShell 7 first, then run the BUILD.md line unchanged
winget install Microsoft.PowerShell
```

Either way it's a one-time setting. Option A is simpler, and 5.1 is what I've been running on the ASUS all along.

## Your sleep plan

Sleeping when idle and waking with the button works fine with SSH. The automatic sleep timer is the risk:

- The ASUS is currently set to **sleep after 4 hours** without keyboard or mouse input. Your CLAUDE.md says 60 minutes, so it has changed since then.
- A training job running over SSH or in a notebook **doesn't count as activity**. A 6-hour training run could be put to sleep at hour 4.
- Suggested habit: turn the timer off and sleep the machine yourself (Start → Power → Sleep) when you're done. From an admin prompt:

```powershell
powercfg /change standby-timeout-ac 0
```

This also matches what BUILD.md line 52 assumed. That line says to disable sleep because the machine is "meant to be always-on"; for you, the reason is to protect long runs rather than to stay always-on.

Nothing in the SSH setup can lock you out of remote desktop, and the shell problem I warned about is easy to undo through remote desktop.

## Why SSH can't cost you remote desktop
SSH and remote desktop are two separate doors into the ASUS, run by two different services on two different network ports:

| | Remote desktop (what you use now) | SSH (what BUILD.md §2 adds) |
|---|---|---|
| Service | Remote Desktop Services | `sshd` (new) |
| Port | 3389 | 22 |
| Touched by §2? | no | yes |

Every command in §2 only installs, starts or configures `sshd`, or opens port 22. None of them changes remote desktop or its firewall rule. If any SSH step goes wrong, the worst outcome is that **SSH doesn't work**, and you're exactly where you are today.

## What the PowerShell 7 line actually risks
When you connect over SSH, `sshd` checks who you are and then starts a shell program for you to type into. The `DefaultShell` registry setting names that program. If it names a file that doesn't exist (`pwsh.exe`, PowerShell 7, isn't installed), `sshd` has nothing to start. The connection closes right after login, every time.

That's all that happens:
- Windows, remote desktop and your files are unaffected.
- To fix it, connect by remote desktop, open an admin PowerShell, and delete the setting:

```powershell
Remove-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell
```

SSH then falls back to cmd.exe and works again. I said it more alarmingly than it deserved.

## A low-risk way to set SSH up
1. Stay connected by remote desktop the whole time, and run the four commands in §2 from an admin PowerShell there.
2. **Skip the `DefaultShell` line entirely for now.** cmd.exe works fine, and you can type `powershell` after logging in.
3. Test from the Surface while remote desktop stays open: `ssh user@ASUS-GPU`.
4. If anything misbehaves, remote desktop is still there to fix it. To undo SSH completely: `Stop-Service sshd; Set-Service sshd -StartupType Disabled`.

## Recovery without SSH, if remote desktop itself broke
I need to correct something I said earlier: I suggested switching a card back from Safe Mode with `nvidia-smi`. That's wrong. Safe Mode doesn't load the NVIDIA driver, and `nvidia-smi` needs it, so the command wouldn't work there.

What does hold:
- **Right now GPU 0 is in WDDM mode.** A monitor and keyboard plugged into GPU 0 would show the normal Windows desktop, so you have a local console today.
- **If all four cards were in TCC,** I'm not sure what a monitor would show after Windows starts, and I haven't tested it. Safe Mode should display through Windows' basic display driver, which lets you repair settings, but it's clumsy.
- **SSH is the cleaner safety net.** If remote desktop ever breaks, you SSH in and fix it. That includes switching a card back to WDDM, which needs the normal driver:

```
nvidia-smi -i 0 -dm 0
```

followed by a reboot.

So the safe order is: **set up SSH first and confirm it works, then switch all four cards to TCC.** Or keep GPU 0 in WDDM as your local-console fallback. That most likely leaves the 0↔1 NVLink pair inactive, which only matters for multi-GPU work you aren't doing yet.

You'll run three admin commands, then reboot. You can type them in the SSH session from the Surface, since an SSH login with an administrator account already has admin rights there. Or use an admin PowerShell in remote desktop. Either works.

## 1. Switch the two WDDM cards to TCC

I'm naming the cards by their PCI address rather than by GPU number, so there's no ambiguity:

```powershell
nvidia-smi -i 00000000:19:00.0 -dm 1
nvidia-smi -i 00000000:1A:00.0 -dm 1
```

Each should print something like `Set driver model to TCC … All done. Reboot required.` The change only takes effect after a reboot, so remote desktop keeps working until then. To confirm it's queued:

```powershell
nvidia-smi --query-gpu=index,pci.bus_id,driver_model.current,driver_model.pending --format=csv
```

All four rows should show `TCC` under *pending*.

## 2. Set up the 150 W power cap to apply at every boot

Doing this now means the caps are in place from the first minute after the reboot:

```powershell
schtasks /create /tn "GPU power cap 150W" /tr "C:\Windows\system32\nvidia-smi.exe -pl 150" /sc onstart /ru SYSTEM /rl HIGHEST
```

It should answer `SUCCESS: The scheduled task … has successfully been created.`

## 3. Reboot

```powershell
shutdown /r /t 0
```

Both remote desktop and SSH will drop. Wait about 2 minutes, then reconnect remote desktop from the Surface as usual. If remote desktop doesn't come back, try `ssh user@ASUS-GPU` from the Surface cmd. That's your fallback, and it lets you undo the change with `nvidia-smi -i 00000000:19:00.0 -dm 0` and a reboot.

## After the reboot

If GPUs 0 and 1 show Code 43 again, rerun the two restart commands from an admin prompt:

```powershell
pnputil /restart-device "PCI\VEN_10DE&DEV_1E30&SUBSYS_129E10DE&REV_A1\6&1497C62D&0&00400000"
pnputil /restart-device "PCI\VEN_10DE&DEV_1E30&SUBSYS_129E10DE&REV_A1\6&238CAF98&0&00800000"
```

Once you're back in, ask me and I'll check:
- all four in TCC,
- both NVLink pairs active (this will tell us whether WDDM was what kept the 0↔1 link down),
- the 150 W caps applied,
- and then a short test with all four cards loaded together, staying at or below about 600 W because of the caps.