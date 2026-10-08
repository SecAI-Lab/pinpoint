# PinPoint Artifact - ACSAC 2026

Artifacts for the paper "Localizing Vulnerabilities under Function Inlining Toward Precise Binary Patching" (ACSAC 2026).

## Overview

This artifact contains the implementation and evaluation code for PinPoint, a system that locates known vulnerable code in a binary even when the compiler has inlined the vulnerable function away. Once a vulnerable callee is absorbed into a larger caller it no longer exists as a routine to match against, so binary code similarity detection (BCSD) models, which work at function granularity, miss it. PinPoint adds a localization layer on top of a pre-trained BCSD model: it ranks the candidate functions of a target binary and reports the byte range of the vulnerable code inside the one it retrieves.

The layer is backbone-agnostic, so the evaluation uses two BCSD models and reports both:

- **BinShot**: BCSD model from S. Ahn, S. Ahn, H. Koo, and Y. Paek, "Practical binary code similarity detection with BERT-based transferable similarity learning," ACSAC 2022.
- **SAFE**: BCSD model from L. Massarelli, G. A. Di Luna, F. Petroni, L. Querzoni, and R. Baldoni, "SAFE: Self-attentive function embeddings for binary similarity," DIMVA 2019.

Both are used with their published weights, without fine-tuning.

**Start here:** [open the notebook in Google Colab](https://colab.research.google.com/drive/1lB3SF1_AJOuVIFm7ot2OvHSsSqhc7NU4?usp=sharing), set Runtime > Change runtime type > T4 GPU, and run the cells in order. They clone this repository, install everything, and run both claims. The notebook ships with the output of our own run, so you can see what to expect before running anything. The same notebook is in this repository as `PinPoint_AE_ACSAC.ipynb`.

## System Requirements

- Linux (tested on Ubuntu 22.04 and on Google Colab)
- Python 3.9 - 3.13 (tested on 3.11 and on 3.13, which is Colab's version)
- PyTorch 2.0+ with CUDA for BinShot, TensorFlow 2 for SAFE; Colab ships both
  (tested on PyTorch 2.11 and TensorFlow 2.20)
- CUDA-capable NVIDIA GPU with 4GB+ VRAM; tested on a free Colab T4 (16 GB)
- 4GB+ system RAM, ~1.5GB disk
- Network: needed once during setup, to clone the backbones and download SAFE's
  weights. The evaluation itself runs offline.
- No GUI, no API keys, no paid services, no commercial software. The only
  licensing constraint is that SAFE's weights are downloaded from the SAFE
  authors rather than redistributed here; see Technical Notes.

## Installation

```bash
git clone https://github.com/SecAI-Lab/pinpoint.git
cd pinpoint
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

Both are run from the repository root.

### Claim 1: PinPoint Retrieval Effectiveness
```bash
bash claims/claim1/run.sh
```

### Claim 2: Vulnerable Code Range Localization
```bash
bash claims/claim2/run.sh
```

Run claim 1 first: claim 2 reuses its results and finishes in seconds.

Optionally, a few minutes to confirm the setup before committing to claim 1's
three hours:

```bash
bash artifact/scripts/smoke.sh
```

## Reproducibility Claims

The requested badge is **Results Reproduced**. Each claim maps to one paper
result, one script, and one expected output:

| Claim | Paper | Script | Data | Expected output |
|---|---|---|---|---|
| 1. PinPoint Retrieval Effectiveness | RQ1, Table III, Section VII-B | `claims/claim1/run.sh` | `artifact/data/` (BinShot) and `artifact/data/safe/` (SAFE) | `claims/claim1/expected/result.txt` |
| 2. Vulnerable Code Range Localization | RQ2, Table IV, Section VII-C | `claims/claim2/run.sh` | claim 1's BinShot results, scored against `artifact/data/ground_truth/` | `claims/claim2/expected/result.txt` |

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

**Claim 1** prints Table III: Top-K retrieval accuracy (K = 1, 5, 10) and MRR,
across the four inlining types (Types I-IV) and overall, with one row for each
of the two backbones standalone and one for each as a PinPoint backbone.

- expected: `claims/claim1/expected/result.txt`
- produced: `claims/claim1/actual/claim1.txt`, beside the four scored tables
  (`topk.*.txt`) and the run logs

**Claim 2** prints Table IV: within-function localization accuracy of the
reported vulnerable code range, per inlining type, with the number of queries
behind each figure.

- expected: `claims/claim2/expected/result.txt`
- produced: `claims/claim2/actual/claim2.txt`, with the per-query detail in
  `claim2.json`

### How to tell whether it worked

Each claim prints one table. **It succeeds when that table matches
`claims/claim*/expected/result.txt`.** On a free Colab T4 it matches exactly: we
obtained identical output on two independent runs. A run that stops with a
traceback, or prints no table, has failed.

One result looks like a failure and is not. PinPoint-SAFE's overall Top-1 is
slightly below standalone SAFE (52.3 -> 51.7). The paper reports the same
(46.1 -> 45.6); SAFE's Top-5, Top-10 and MRR all rise, and the gain the paper
claims is in Type II, which rises for both backbones (40.8 -> 55.7 for BinShot,
8.4 -> 15.0 for SAFE) and is the largest of the four types in both cases.

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
- One source of nondeterminism, for SAFE only: where a target function is shorter than
  the sliding window, two stages see the same tokens and their scores tie, so which stage
  is credited depends on the TensorFlow build. This moves a stage label in the per-query
  report, never a score or a rank, so Table III is unaffected.

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
