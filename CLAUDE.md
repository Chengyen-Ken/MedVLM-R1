# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project

Reproducing [MedVLM-R1](https://github.com/JZPeterPan/MedVLM-R1) (Pan et al., MICCAI 2025, arXiv:2502.19634) as a first phase, before extending it with original research. This repo is a fork of the original — `origin` is the fork (`Chengyen-Ken/MedVLM-R1`), `upstream` is `JZPeterPan/MedVLM-R1`. Deadline for the reproduction phase is around 2026-11-11.

## Target environment

- Cluster: NSCC Singapore, ASPIRE2A (4x A100-40GB per node, PBS Pro queue `"ai"`)
- Project ID: `csyuchen` (use `-P csyuchen` for `qsub`)
- Setup runbook and PBS job script: `docs/nscc-setup.md`, `nscc/setup_env.sh`, `nscc/train.pbs`. `train_script.sh` (upstream) assumes an already-live `torchrun` rendezvous (`MASTER_ADDR`/`MASTER_PORT` supplied externally) and isn't PBS-Pro-aware, so `nscc/train.pbs` reimplements its invocation with real values rather than wrapping it — reconcile manually if `upstream` changes `train_script.sh`.
- Training data: the README's `PubMedVision` download instructions are wrong for the `Huatuo` branch `grpo.py` actually uses — confirmed by full census, the real image source is `foreverbeliever/OmniMedVQA` (single 10.7GB zip, no partial download). `nscc/omnimedvqa_manifest.json` + `nscc/verify_dataset.py` turn "will this work" into a found/missing count in minutes — still open whether the specific 1,500 needed images are in OmniMedVQA's open-access or gated bucket, unknowable without downloading. See `docs/nscc-setup.md` step 3.

## Storage layout

`$HOME` is `/home/users/ntu/csyuchen`. `$HOME/scratch` is the scratch root — deliberately **shared across all NSCC projects**, not namespaced to this one, so future projects reuse the same datasets/envs instead of re-downloading:

```
$HOME/scratch/
├── envs/medvlm-r1/                       this project's conda env
├── datasets/{omnimedvqa,...}/            raw datasets, reusable across projects
├── hf_cache/                             shared HF_HOME
└── checkpoints/medvlm-r1/<run-name>/     training output, namespaced per project

$HOME/reproduce/MedVLM-R1/                this repo (persistent code, not scratch)
$HOME/project/<future-name>/              where original-research projects go later
```

Reproduction phase (current): conda env, dataset, and checkpoints all accept NSCC's 30-day scratch inactivity-purge as a deliberate simplicity-over-durability tradeoff — everything there is regenerable (env via `nscc/setup_env.sh`, dataset via the HF CLI download, checkpoints via re-running training). Code lives in `$HOME/reproduce/MedVLM-R1`, not scratch. `nscc/setup_env.sh` and `nscc/train.pbs` reference these paths via `$HOME`, already wired up.

Once the project moves from reproduction into original research (`$HOME/project/<name>`), switch to keeping checkpoints and results outside scratch instead.

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root, created lazily as needed. See `docs/agents/domain.md`.
