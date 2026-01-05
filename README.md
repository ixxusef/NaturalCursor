# NaturalCursor

> Human-behavior utilities for Playwright enabling low-detectability browser automation.

---

## Why This Exists

Modern bot detection systems can't use traditional detection anymore. With modern emulation libraries like Playwright, they now have to look for **unrealistic input**.

Playwright provides amazing speed and control, but default automation behavior is:
- perfectly linear
- perfectly timed
- perfectly inhuman

This library provides **human-behavior primitives** that make automated browser interactions smoother in an efficient, scalable way.

---

## Features

- 🖱️ Human-like mouse movement (curves, overshoot, correction)
- ⌨️ Realistic typing (delays, typos, corrections)
- ⏱️ Natural timing variance and idle input
- 🧭 Cursor state tracking
- 🎭 Drop-in Playwright compatibility
- 🔌 Modular utilities — use only what you need

---

## Installation
Coming soon. For now, you can clone the code repository. 
```bash
pip install NaturalCursor
