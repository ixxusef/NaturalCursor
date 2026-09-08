# NaturalCursor

> Human-behavior primitives for Playwright. Built to test and research bot-detection systems.

## Why this exists

Bot detection is a black box. Cloudflare, Google, and Microsoft don't publish how their systems work, so when I ship a client application with detection wired in (especially when the API is the product), I have no reliable way to verify the protections actually hold. The usual workaround is turning detection off during testing. That's how blind spots ship.

NaturalCursor lets me test with detection left on, exactly as configured in production. It generates realistic mouse movement, typing, and timing so I can catch edge cases and crashes before an attacker finds them.

It's also half of a research project. I'm building an open-source, ML-based bot-detection algorithm, and you can't build a detector without a realistic adversary to train and test against. Every heuristic approach I've tried fails to tell NaturalCursor apart from a real user, and everyone I've consulted has hit the same wall. That's why the detection side has to be machine learning. This library is the adversary that detector trains against.

### Results so far

Nothing I've tested catches it. That includes Google, Cloudflare, and Microsoft. This result is the reason the detector project exists: rule-based detection has hit a ceiling against behavior-level emulation, and I think the fix is machine learning, published open source so anyone can use it.

## What it does

Playwright gives you speed and control, but its default input is easy to fingerprint:

- linear: the pointer moves in straight lines or teleports
- timed: events fire at machine-regular intervals
- inhuman: no hesitation, no overshoot, no correction

NaturalCursor replaces those signatures:

- Human-like mouse movement (curves, overshoot, correction)
- Realistic typing (delays, typos, corrections)
- Natural timing variance and idle input
- Cursor state tracking
- Drop-in Playwright compatibility
- Modular utilities, load only what you need

## Intended use

Use this on applications you own or have permission to test. It's built for edge-case and crash detection with production security left on, for QA under realistic conditions, and for adversarial detection research. If you point it at infrastructure that isn't yours, that's on you.

## Installation

Coming soon:

```bash
pip install NaturalCursor
```

Until then, clone the repo.

## Roadmap

- [ ] PyPI release
- [ ] Companion project: open-source ML detection algorithm
- [ ] Docs and examples
