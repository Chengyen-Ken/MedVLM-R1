# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project

Reproducing [MedVLM-R1](https://github.com/JZPeterPan/MedVLM-R1) (Pan et al., MICCAI 2025, arXiv:2502.19634) as a first phase, before extending it with original research. This repo is a fork of the original — `origin` is the fork (`Chengyen-Ken/MedVLM-R1`), `upstream` is `JZPeterPan/MedVLM-R1`. Deadline for the reproduction phase is around 2026-11-11.

## Target environment

- Cluster: NSCC Singapore, ASPIRE2A (4x A100-40GB per node, PBS Pro queue `"ai"`)
- Project ID: `csyuchen` (use `-P csyuchen` for `qsub`)
- Setup runbook and PBS job script: `docs/nscc-setup.md`, `nscc/setup_env.sh`, `nscc/train.pbs`. `train_script.sh` (upstream) assumes an already-live `torchrun` rendezvous (`MASTER_ADDR`/`MASTER_PORT` supplied externally) and isn't PBS-Pro-aware, so `nscc/train.pbs` reimplements its invocation with real values rather than wrapping it — reconcile manually if `upstream` changes `train_script.sh`.
- Open question: the training data path. `grpo.py`'s `Huatuo` branch loads metadata from `FreedomIntelligence/Medical_Multimodal_Evaluation_Data`, not the `PubMedVision` dataset the README's download instructions reference — whether PubMedVision's files satisfy the image paths `grpo.py` expects is unverified. See `docs/nscc-setup.md` step 3 before downloading anything.

## Storage layout

Reproduction phase (current): conda env, dataset, and checkpoints all live under `/scratch`, accepting NSCC's 30-day inactivity purge as a deliberate simplicity-over-durability tradeoff — everything there is regenerable (env via `setup.sh`, dataset via the HF CLI download, checkpoints via re-running training). Code lives in the persistent project directory (`/home/project/csyuchen/`), not scratch.

Once the project moves from reproduction into original research, switch to keeping checkpoints and results in the persistent project directory instead of scratch.

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root, created lazily as needed. See `docs/agents/domain.md`.
