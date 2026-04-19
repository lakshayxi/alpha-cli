# alpha-cli 🚀

A lightweight, high-performance Python CLI for autonomous WorldQuant Brain alpha mining using Cloud LLMs.

## Features
- **Cloud-Powered:** Use GPT-4o, Claude 3.5 Sonnet, or Gemini 1.5 Pro for intelligent alpha generation.
- **Interactive Setup:** Professional setup wizard for secure credential management.
- **Autonomous Mining:** Continuous loop that generates, validates, simulates, and optimizes alphas.
- **Surgical Correction:** Automatically fixes common WorldQuant Brain errors (parameter counts, event-input compatibility).
- **Settings Optimization:** Near-passing alphas are automatically tuned (lookback, decay, truncation).
- **Semantic Validation:** Catches anti-patterns and unit mismatches before submitting simulations.

## Installation
1. Navigate to the `alpha_cli` directory.
2. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Initial Setup
Run the interactive setup wizard to configure your AI provider and WorldQuant Brain credentials:
```bash
python -m alpha_cli.cli.main setup
```

### 2. Start Mining
Launch the autonomous mining loop for a specific region:
```bash
python -m alpha_cli.cli.main mine start --region USA --iterations 20
```

### 3. View Results
Browse your simulation history and top-performing alphas:
```bash
python -m alpha_cli.cli.main results view --min-sharpe 1.0
```

## Core Intuition (Learnings from Chat)
- **Surgical Fixes:** The system padds missing parameters to exact operators (e.g., `trade_when(x) -> trade_when(x, 1, 1)`).
- **Event Mapping:** Swaps incompatible operators like `inverse` to `ts_rank` when event data fields are detected.
- **Resilient Polling:** Correctly handles WorldQuant's "silent" progress updates and explicit FAIL statuses.
