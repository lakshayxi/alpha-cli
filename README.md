# alpha-cli

A professional, high-performance command-line interface for autonomous WorldQuant Brain alpha discovery using Cloud LLM agents.

## Overview

The alpha-cli is a research-oriented discovery engine that orchestrates Large Language Models (Gemini, Claude) to design, validate, and simulate quantitative trading signals (alphas). Unlike traditional systems, alpha-cli functions as a delegated wrapper, leveraging the reasoning capabilities of local agent CLIs to perform complex financial engineering tasks without the overhead of manual API key management.

## Key Technical Features

### 1. Delegated Agent Architecture
The system integrates directly with local 'gemini' and 'claude' (Claude Code) CLI installations. This allows for a keyless authentication model, utilizing existing authenticated sessions on the host machine to perform high-level research and signal generation.

### 2. Reflective Memory & Heuristic Synthesis
Alpha-cli implements a self-learning loop that mirrors human research patterns:
*   **Observation:** The system records exhaustive telemetry for every simulation, including detailed error signatures.
*   **Pattern Synthesis:** A dedicated analysis layer identifies recurring mathematical motifs in successful alphas and systemic failure modes in rejected ones.
*   **Dynamic Knowledge Injection:** Synthesized heuristics are injected back into the LLM's system prompt in real-time, allowing the engine to evolve its strategy based on empirical evidence.

### 3. Surgical Self-Correction
The engine features a deterministic validation layer designed to handle WorldQuant's FASTEXPR syntax. It performs surgical corrections on generated expressions, such as:
*   **Parameter Alignment:** Automatically resolving 'Invalid number of inputs' errors by padding or truncating operator arguments based on live API feedback.
*   **Event Compatibility:** Dynamically swapping incompatible operators (e.g., 'inverse' to 'ts_rank') when event-based data fields are detected.

### 4. Robust Simulation Management
*   **API Resilience:** Implements a two-stage data discovery pipeline to bypass broad query rejections (400 errors).
*   **Terminal Polling Logic:** Handles WorldQuant's non-standard API states, correctly identifying 'silent' progress updates and explicit FAIL statuses to prevent infinite polling loops.
*   **Sequential Optimization:** Near-passing alphas are automatically routed through a multi-stage optimization framework, tuning lookback windows, decay, and truncation parameters.

## Architecture

The project follows a standard professional src-layout:

```
alpha-cli/
├── src/
│   └── alpha_cli/
│       ├── cli/        # Command-line interface and interactive wizards
│       ├── core/
│       │   ├── brain/  # WorldQuant Brain API communication and simulation
│       │   ├── llm/    # Agent CLI delegation and JSON extraction logic
│       │   ├── storage/# Persistence and Reflective Memory systems
│       │   └── engine/ # Discovery orchestrator and optimization logic
│       └── config/     # Secure configuration and credential management
└── README.md
```

## Installation

### Prerequisites
*   Python 3.8 or higher.
*   An active WorldQuant Brain account.
*   An authenticated installation of either the Gemini CLI or Claude Code.

### Setup
1. Clone the repository.
2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Configuration
Run the setup wizard to configure your preferred AI agent and WorldQuant Brain credentials:
```bash
alpha-cli setup
```

### 2. Autonomous Mining
Launch the discovery loop. The system will automatically fetch market context, generate ideas, and perform simulations:
```bash
alpha-cli mine start --region USA --iterations 10
```

### 3. Performance Analysis
View and filter your simulation history from the local SQLite database:
```bash
alpha-cli results view --min-sharpe 1.25
```

## Storage
Historical data, identified heuristics, and simulation metrics are stored locally in the following directory:
`~/.alpha-cli/`

## License
This project is intended for quantitative research and educational purposes on the WorldQuant Brain platform.
