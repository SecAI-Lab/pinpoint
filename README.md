# PinPoint Artifact - ACSAC 2026

Artifacts for the paper "Localizing Vulnerabilities under Function Inlining Toward Precise Binary Patching" (ACSAC 2026).

## Overview

This artifact contains the implementation and evaluation code for PinPoint, a vulnerability localization system that works when the compiler has inlined the vulnerable function away. Once a vulnerable callee is absorbed into a larger caller, it no longer survives as a routine with a boundary, and binary code similarity detection (BCSD) models, which operate at function granularity, miss it. PinPoint adds a backbone-agnostic localization layer on top of a pre-trained BCSD model: it ranks the candidate functions of a target binary and reports the byte range of the vulnerable code inside the one it retrieves.

PinPoint is backbone-agnostic, so the evaluation uses two BCSD backbones and reports both:

- **BinShot**: BCSD model from S. Ahn, S. Ahn, H. Koo, and Y. Paek, "Practical binary code similarity detection with BERT-based transferable similarity learning," ACSAC 2022.
- **SAFE**: BCSD model from L. Massarelli, G. A. Di Luna, F. Petroni, L. Querzoni, and R. Baldoni, "SAFE: Self-attentive function embeddings for binary similarity," DIMVA 2019.

Both are used with their published weights, without fine-tuning.

## System Requirements

- Python 3.9 or newer (tested on 3.11 and on 3.13, which is Colab's version)
- PyTorch for BinShot, TensorFlow for SAFE; Colab ships both
- CUDA-compatible GPU, 2GB+ VRAM; a free Colab T4 is what this was sized for
- 4GB+ system RAM, ~1.5GB disk

## Installation

```bash
./install.sh
```

This script installs the dependencies, clones both backbones, unpacks the packaged data, downloads SAFE's weights, precomputes the BinShot reference embeddings, and verifies the layout. It is safe to re-run.

No disassembler is needed at evaluation time: Ghidra and radare2 analysis and DWARF ground-truth extraction are done offline and shipped as JSON.

## Quick Start

A smoke test first, to confirm the setup works before committing to the long run:

```bash
bash artifact/scripts/smoke.sh
```

Then the two reproducibility claims:

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

Run claim 1 first. Claim 2 reuses its cascade results and then finishes in seconds.

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
- Top-K retrieval accuracy and MRR, per inlining type (Types I-IV) and overall, for each of
  the two backbones standalone and as a PinPoint backbone (paper Table III)
- Within-function localization accuracy per inlining type, with the number of queries
  behind each figure (paper Table IV)

Expected outputs are provided in `claims/claim*/expected/result.txt` for comparison.

## Technical Notes

Due to computational constraints for artifact evaluation:
- The packaged subset is 32 of the corpus's 300 target binaries, sized so that both backbones
  finish inside one Colab session. Do not cut it down further; `use.txt` explains why.
- Four of the nine projects (binutils, jasper, libarchive, libxml2) are excluded, as their
  cheapest binaries each cost more GPU time than the rest of the subset together.
- Trex and the two graph-based baselines of Table III are not packaged.
- Efficiency results (pruning speedup, amortized latency) are not reproduced; they characterize
  a full-corpus run.
- SAFE is published without a licence, so install.sh downloads its weights from the SAFE
  authors' own distribution. BinShot is MIT and its weights ship in the data bundle.
- Results may show numerical differences from the paper but demonstrate the same trends.
  `use.txt` states the limits in full.

## Directory Structure

```
artifact/                   # Main implementation code
  pinpoint.py               # Entry point; runs the cascade over a corpus
  backbone.py               # Model loading, tokenization, containment count
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
README.txt                  # This file
use.txt                     # Usage guidelines and limitations
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

Every window scored in Stages 2 and 3 is dumped to `results/cascade/<db>/result_<target>_windows.jsonl.gz`, so a run can be inspected window by window. `--help` lists the rest.

## Evaluation Time

| | time |
|---|---|
| Smoke test | a few minutes |
| Claim 1 (two backbones, two configurations each) | about 3 hours on a Colab T4 |
| Claim 2 (reuses claim 1's run) | seconds |

Measured on a free Colab T4: BinShot 1h15m for the cascade plus 6m for the Stage 1 baseline, SAFE 1h35m plus 7m.

Runs are resumable within a session: a target whose report already exists is skipped. A Colab session that is torn down takes `/content` with it, and the run then starts over.

## Troubleshooting

**`operator torchvision::nms does not exist` on import.** torch and torchvision are from different builds. Reinstall them together, or let Colab's preinstalled pair stand.

**A target is skipped and the totals show `locked=1`.** A previous run left a lock file. Delete `results/**/*.lock`; the claim runners do this themselves.

**The run is very slow.** Check that a GPU is attached (`torch.cuda.is_available()`) and that `artifact/data/reference_embeddings/` exists.

**Out of disk on Colab.** Clearing `artifact/results/` between runs frees the largest part.

## Full Corpus

The complete corpus, 300 target binaries and their -fno-inline builds against a 577-entry reference database over 73 CVEs from nine projects, with the raw outputs of the paper's own run, is archived separately with a DOI. `artifact/scripts/build_eval_subset.py` takes an explicit binary list, so the subset can be widened or the whole corpus reproduced.

## Contact

For questions about this artifact, please refer to the paper or contact the authors through the conference proceedings.
