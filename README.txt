# PinPoint Artifact - ACSAC 2026

Artifacts for the paper "Localizing Vulnerabilities under Function Inlining Toward Precise Binary Patching" (ACSAC 2026).

## Overview

This artifact contains the implementation and evaluation code for PinPoint, a system that locates known vulnerable code in a binary even when the compiler has inlined the vulnerable function away. Once a vulnerable callee is absorbed into a larger caller it no longer exists as a routine to match against, so binary code similarity detection (BCSD) models, which work at function granularity, miss it. PinPoint adds a localization layer on top of a pre-trained BCSD model: it ranks the candidate functions of a target binary and reports the byte range of the vulnerable code inside the one it retrieves.

The layer is backbone-agnostic, so the evaluation uses two BCSD models and reports both:

- **BinShot**: BCSD model from S. Ahn, S. Ahn, H. Koo, and Y. Paek, "Practical binary code similarity detection with BERT-based transferable similarity learning," ACSAC 2022.
- **SAFE**: BCSD model from L. Massarelli, G. A. Di Luna, F. Petroni, L. Querzoni, and R. Baldoni, "SAFE: Self-attentive function embeddings for binary similarity," DIMVA 2019.

Both are used with their published weights, without fine-tuning.

**Start here:** open `PinPoint_AE_ACSAC.ipynb` in Google Colab (link in `infrastructure/colab_link.txt`) and run the cells in order. It clones this repository, installs everything, and runs both claims. The notebook ships with the output of our own run, so you can see what to expect before running anything.

## System Requirements

- Python 3.9 or newer (tested on 3.11 and on 3.13, which is Colab's version)
- PyTorch for BinShot, TensorFlow for SAFE; Colab ships both
- CUDA-compatible GPU with 2GB+ VRAM; a free Colab T4 is enough
- 4GB+ system RAM, ~1.5GB disk

## Installation

Run the installation script to set up all dependencies:

```bash
./install.sh
```

This script will:
- Install the required Python packages
- Clone the BinShot and SAFE backbones
- Unpack the packaged data and download SAFE's weights
- Precompute the BinShot reference embeddings
- Verify the layout

It is safe to re-run.

No disassembler is needed. Ghidra and radare2 recovery and DWARF ground-truth extraction are done offline, and their output ships as JSON.

## Quick Start

The artifact contains two reproducibility claims:

### Claim 1: PinPoint Retrieval Effectiveness
```bash
cd claims/claim1
./run.sh
```

### Claim 2: Vulnerable Code Range Localization
```bash
cd claims/claim2
./run.sh
```

Run claim 1 first: claim 2 reuses its results and finishes in seconds.

Optionally, a few minutes to confirm the setup before committing to claim 1's
three hours:

```bash
bash artifact/scripts/smoke.sh
```

## Reproducibility Claims

For each major paper result evaluated under the "Results Reproduced" badge:

```
claims/claim1/
    |------ claim.txt    # Brief description of the paper claim (Table III)
    |------ run.sh       # Script to produce result
    |------ expected/    # Expected output or validation info
claims/claim2/
    |------ claim.txt    # Brief description of the paper claim (Table IV)
    |------ run.sh       # Script to produce result
    |------ expected/    # Expected output or validation info
```

## Expected Results

Each claim generates evaluation results showing:
- Top-K retrieval accuracy (K = 1, 5, 10) and MRR
- Within-function localization accuracy of the reported vulnerable code range
- Results across the four inlining types (Types I-IV) and overall
- Comparison across different backbones (BinShot, SAFE), each standalone and as a PinPoint backbone

Expected outputs are provided in `claims/claim*/expected/result.txt` for comparison.

## Technical Notes

Due to computational constraints for artifact evaluation:
- The packaged subset is 32 of the corpus's 300 target binaries, sized so that both backbones
  finish inside one Colab session. Do not cut it down further; `use.txt` explains why.
- Four of the nine projects (binutils, jasper, libarchive, libxml2) are excluded, as their
  cheapest binaries each cost more GPU time than the rest of the subset together.
- Trex and the two graph-based baselines of Table III are not packaged.
- Efficiency results (pruning speedup, amortized latency) are not reproduced; they are a
  property of a full-corpus run.
- SAFE is published without a licence, so install.sh downloads its weights from the SAFE
  authors' own distribution. BinShot is MIT and its weights ship in the data bundle.
- Results may show numerical differences from the paper but demonstrate the same trends.
  `use.txt` states the limits in full.

## Directory Structure

```
artifact/                   # Main implementation code
  pinpoint.py               # Entry point; runs the cascade over a corpus
  backbone.py               # Model loading, tokenization, window selection
  size_based_pruning.py     # Size-ratio pruning, before the cascade
  stage1_whole_function.py  # Stage 1: whole-function comparison
  stage2_block_stride.py    # Stage 2: block-stride search
  stage3_token_stride.py    # Stage 3: token-stride search
  evaluate.py               # Vulnerable code range scoring (claim 2)
  safe/                     # The same cascade over the SAFE backbone
  analysis/                 # The paper's own Top-K table code (claim 1)
  scripts/                  # Smoke test, data fetch, subset derivation
  data/                     # Targets, reference DBs, ground truth
    safe/                   # The same binaries in SAFE's own representation
  models/                   # Backbone weights and vocabularies

claims/                     # Reproducibility claims
  claim1/                   # PinPoint retrieval effectiveness
  claim2/                   # Vulnerable code range localization

infrastructure/             # Colab link and platform requirements
install.sh                  # Installation script
README.md, README.txt       # This file, in two formats
use.txt                     # Intended use and limitations
provenance.txt              # Where the data came from and how it was derived
ethics.txt                  # Ethics of the data collection
license.txt                 # MIT License, including third-party
metadata.toml               # ACSAC artifact metadata (artmeta)
PinPoint_AE_ACSAC.ipynb     # Colab notebook
```

## Running Individual Experiments

```bash
cd artifact

# one project, one stage
python3 pinpoint.py --project libtiff --stage 3

# turn off size-ratio pruning and watch the candidate count grow
python3 pinpoint.py --no-filter --overwrite

# the type-wise Top-K tables for a run
python3 analysis/topk_table.py --db-dir results/cascade --out /tmp/topk.txt

# the same cascade over the SAFE backbone, one binary
python3 safe/run_safe.py --only libming-listmp3-64-clang-O2 --output_dir /tmp/safe
```

Stages 2 and 3 write every window they score to `results/cascade/<db>/result_<target>_windows.jsonl.gz`, so a finished run can be inspected window by window. `--help` lists the rest.

## Evaluation Time

Each claim evaluation takes approximately:
- Smoke test: a few minutes on single GPU
- Claim 1 (both backbones): about 3 hours on single GPU
- Claim 2 (reuses claim 1's run): seconds

Times may vary based on hardware configuration.
