<div align="center">

# 🚀 Antigravity CLI Manager (acm)

[![test](https://github.com/hiri-dev/antigravity-cli-manager/actions/workflows/test.yml/badge.svg)](https://github.com/hiri-dev/antigravity-cli-manager/actions/workflows/test.yml)
[![Bash](https://img.shields.io/badge/Bash-%23121011.svg?style=for-the-badge&logo=gnu-bash&logoColor=white)](#)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](#)

*A lightweight, elegant Terminal UI (TUI) to manage and hot-swap Google Gemini account sessions for the `agy` CLI utility.*

![Antigravity CLI Manager Screenshot](Screenshot.png)

</div>

---

## ✨ Features

- **🎨 Retro Terminal UI**: Clean interface built entirely in Bash with Unicode box frames, beautiful ASCII art, and ANSI colors.
- **⚡ Background Quota Sync**: Automatically fetches Gemini API limits silently in the background on startup.
- **⭐ Best Account Indicator**: Automatically calculates and highlights (`★`) the account with the highest remaining quota.
- **🛡️ Secure Design**: Obfuscated credentials, secure environment variable handovers, and scoped temp handlers to eliminate shell injection surfaces.
- **🔐 OAuth Login Capturer**: Auto-captures OAuth tokens directly from the browser flow and closes the login instance gracefully.
- **⚙️ Hot-Swapping**: Switch active accounts in seconds and jump right into your next `agy` session.
- **🤖 Auto-Rotation Mode**: Automatically swaps active profiles when the current one runs out of API quota.

## 🚀 Quick Start

### Installation

**Arch Linux (AUR)**:
```bash
git clone https://aur.archlinux.org/antigravity-cli-manager-git.git
cd antigravity-cli-manager-git
makepkg -si
```

**Standard Bash (Manual)**:
```bash
git clone https://github.com/hiri-dev/antigravity-cli-manager.git
cd antigravity-cli-manager
./install.sh
```

To install the modular version (separate Bash UI and Python core helper):
```bash
./install.sh --modular
```

To launch the manager from anywhere, simply run:
```bash
acm
```

## 🤖 Auto-Rotation & CLI Wrapper

`acm` includes an automated rotation mode to automatically swap to the account with the highest remaining quota when your active session hits 0% quota.

### Manual Rotation Trigger
You can force a check and swap at any time by running:
```bash
acm rotate
```

### Execution Wrapper
Run any command (such as `agy`) via the `acm run` wrapper. It will automatically check your quota, swap to the best account if needed, and run your command:
```bash
acm run agy "Explain quantum computing in one sentence"
```

## 🕹️ Usage & Keybindings

Navigation in the `acm` TUI is designed to be quick and intuitive. 

| Key | Action |
| --- | --- |
| `W` / `S` | Navigate Up / Down |
| `Enter` | Launch the selected account in `agy` |
| `d` | Delete the highlighted account |

## ⚙️ Configuration

`acm` supports a lightweight configuration file automatically generated at `~/.config/acm/config.json`.

```json
{
    "show_ascii_art": true,
    "timeout_seconds": 3
}
```

- `show_ascii_art`: Toggle the retro ASCII header (`true`/`false`) to save vertical terminal space.
- `timeout_seconds`: Network timeout threshold for background API quota checks.

## 📦 Requirements

- **Bash 4.0+**
- **Python 3**
- **cURL**
- **`agy`** (Antigravity CLI installed in your `PATH`)

---

<div align="center">
<i>Built with ☕ for power-users who hate hitting API limits.</i>
</div>
