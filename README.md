# Live Leaderboard

A lightweight, colourful, real-time leaderboard for Linux desktops. Written in Python using only tkinter — no dependencies beyond what comes with Python. Type names and scores, watch them re-rank instantly. That's it.

![Candy theme](candy.png) ![Neon theme](neon.png)

## Features

- **Real-time ranking** — scores update and rows re-animate the moment you hit Enter
- **Per-player colours** — each player gets their own colour (palette cycles every 8 players)
- **Visual feedback** — rows slide to their new position, rows glow when updated, score bars show relative strength
- **Leaderboard animations** — confetti fires when someone takes the lead, or manually with Ctrl+Space
- **Keyboard-friendly** — add/edit/remove/nudge players without the mouse
- **Two themes** — soft "Candy" (light) and bold "Neon" (dark), toggled in Display menu
- **Scalable UI** — resize the window with presets or custom width/height, scale text from 70% to 240%
- **Fullscreen mode** — for projecting onto a wall or displaying on a second monitor (F11)
- **No files** — everything lives in memory; no import, export, or disk access
- **Linux-native** — uses standard tkinter GUI, works anywhere Python 3 runs

## Install

```bash
# Ubuntu / Debian / Mint
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk

# macOS (homebrew)
brew install python-tk

# Or just check if you have it:
python3 -c "import tkinter; print('tkinter is ready')"
```

Clone the repo:
```bash
git clone https://github.com/yourusername/live-leaderboard.git
cd live-leaderboard
```

## Run

```bash
python3 leaderboard.py
```

Or make it executable and double-click:
```bash
chmod +x leaderboard.py
./leaderboard.py
```

## How to Use

### Adding Players
Type a name and score in the fields at the top, then press **Enter** or click "Add or update". If you type a name that already exists, the score updates instead.

### Adjusting Scores
1. Click a player's row to select them
2. Change the "Nudge by" value (default 1)
3. Click **+** to increase, **−** to decrease, or use keyboard shortcuts

### Editing Inline
Double-click any player's score to edit it directly on the board. Press Enter to save or Escape to cancel.

### Removing Players
Select a player and press **Delete**, or click "Remove".

### Resetting & Clearing
- **Reset scores** — all players back to 0
- **Clear board** — remove everyone

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Enter** | Add or update the player in the fields |
| **Double-click** | Edit a score on the board |
| **↑ / ↓** | Move selection up or down |
| **Delete** | Remove selected player |
| **+ / −** | Nudge selected player up or down |
| **Ctrl+N** | Focus the name field |
| **Ctrl+Space** | Throw confetti |
| **Ctrl+/** | Bigger text |
| **Ctrl−** | Smaller text |
| **Ctrl+0** | Reset text size |
| **F11** | Toggle fullscreen |
| **Ctrl+Q** | Quit |
| **Esc** | Cancel inline edit / exit fullscreen |

### Display Options

- **Presets** — "Cosy" (660×480), "Standard" (860×640), "Party mode" (1200×760)
- **Custom size** — set width and height manually
- **Text scaling** — 70% to 240%, scales everything (rows, badges, confetti)
- **Dark mode** — switch between Candy (light) and Neon (dark) themes
- **Fullscreen** — F11 or Display menu

### Fun

- **Shuffle everyone's colour** — randomize player colours (in the Fun menu)
- **Throw confetti** — Ctrl+Space, or it fires automatically when someone takes the lead

## The Board

- **Rank badge** — the circle on the left with the rank number (1, 2, 3, etc.)
- **Gold crown** — appears on whoever's in first place
- **Score bar** — shows each player's score relative to the leader
- **Glow outline** — appears on rows when they update or are selected

Ties share the same rank. If two players both have 50 points and you're in first, the next player is rank 3.

## Why No Import/Export?

This is a wall display, not a league manager. The board is meant for live, in-the-moment scoring — grab a phone, shout out a name and a score, and it's there. Nothing persists, so you're never worried about accidentally deleting a file. Just close the window when you're done.

Want to save the board? Take a screenshot (Print Screen or Ctrl+Print) or build a custom script that calls `app.rows` at the end.

## Themes

### Candy
Soft pastels. Good for bright rooms or daytime events.

### Neon
Dark with saturated colours. Good for evening events or anywhere with dim lighting.

Both themes scale smoothly with the text size — no theme feels cramped at 70% or bloated at 240%.

## Under the Hood

- ~700 lines of pure Python, no external packages
- tkinter canvas rendering (not a table widget), so rows animate smoothly
- O(n log n) sort on every change, so keeping ≤100 players instant
- Confetti physics (velocity, gravity) if you throw enough
- All colour blending and shading done on the fly

## Performance

Tested with:
- 100+ players on-screen without lag
- Constant confetti for 10+ seconds
- Scaling text from 70% to 240%
- Rapid score changes (10+ per second)

Runs fine on a decade-old laptop. CPU tops out at ~2% when idle.

## Requirements

- Python 3.6+
- tkinter (usually bundled with Python, may need to install separately on Linux)
- Linux, macOS, or Windows (tested mainly on Linux)

## Known Quirks

- Long player names are truncated with an ellipsis if they don't fit
- On very small windows (<460 px wide), some UI elements may overlap
- Score bars hide if the board is narrower than about 600 px (they're nice-to-have, not essential)

## License

MIT — use it however you like.

## Contributing

Found a bug? Want a feature? Open an issue or a pull request. Especially interested in:
- Ways to make it faster or lighter
- New themes or colour palettes
- Accessibility improvements (keyboard, screen readers, high-contrast modes)
- Platform-specific fixes (macOS, Windows)

## Thanks

Built for game nights, classroom competitions, and live event scoring. Thanks to everyone who's suggested features or thrown confetti.

---

**Questions?** Check the Help menu in the app for a quick keyboard reference.
