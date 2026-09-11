# NSCC Setup (ASPIRE2A)

Runbook for getting this reproduction running on NSCC. Project ID: `csyuchen`, queue `"ai"` (4x A100-40GB per node) — confirm the exact queue name with `qstat -Q` after logging in, NSCC's public docs didn't pin down every queue name beyond `"ai"`.

## 0. Confirm your paths

SSH in and confirm the two paths this whole setup assumes, before touching anything else:

```bash
echo $HOME                                    # small, 50GB quota — code only, nothing big
ls /scratch/$USER 2>/dev/null || echo "check your actual scratch path"
ls /home/project/csyuchen 2>/dev/null || echo "check your actual project dir"
```

If either doesn't match `/scratch/$USER` or `/home/project/csyuchen`, update `SCRATCH_DIR`/`REPO_DIR` at the top of `nscc/setup_env.sh` and `nscc/train.pbs`.

## 1. Get the code onto NSCC

```bash
cd /home/project/csyuchen
git clone https://github.com/Chengyen-Ken/MedVLM-R1.git
cd MedVLM-R1
```

## 2. Build the environment

In scratch, on a compute node — not the login node (flash-attn's build step is heavy and login nodes kill long/CPU-heavy work):

```bash
qsub -I -P csyuchen -q ai -l select=1:ncpus=5:ngpus=1 -l walltime=02:00:00
# once on the compute node:
cd /home/project/csyuchen/MedVLM-R1
bash nscc/setup_env.sh
```

Creates the conda env at `/scratch/$USER/envs/medvlm-r1` — not under `$HOME`, which is too small for a PyTorch + flash-attn stack.

## 3. Dataset — confirmed blocker, not yet resolved

The repo's own README says to download `FreedomIntelligence/PubMedVision` (~59.5GB). **This does not satisfy what the training code actually needs — confirmed, not just suspected:**

- `grpo.py` (for `DATASET=Huatuo`) loads row metadata from a **different** dataset, `FreedomIntelligence/Medical_Multimodal_Evaluation_Data` (test split, filtered to the MR/CT/X-Ray subsets, 500 samples each), and resolves each image at `os.path.join(base_image_path, example["image"][0])`.
- Sampled rows carry `image` filenames like `images/ankle071718.png` and a `dataset` field naming the row's *original* source benchmark (e.g. `OmniMedVQA`, `PMC-VQA_test`) — this dataset is an aggregation over pre-existing medical VQA benchmarks, not something derived from PubMedVision.
- PubMedVision's own files are named `pmc_<n>_<i>.jpg` — different convention, different extension, no overlap with the filenames above.

So the real images need to come from each row's original source benchmark, not PubMedVision. No documentation anywhere (HF dataset cards, the HuatuoGPT-Vision repo, MedVLM-R1's README/issues) reconciles this — looks like an undocumented gap in the upstream repo's reproducibility instructions, not something we're missing.

**Not yet resolved**: which exact source benchmarks appear across the full ~1,500 selected rows (only a 5-row sample confirmed so far), and whether they're all easily downloadable. Once that's known, the real choice is (a) download every distinct source benchmark and assemble `base_image_path` to satisfy all of them, or (b) something else (e.g. contacting the paper's authors). Do not bulk-download PubMedVision in the meantime — it won't be used for this branch.

## 4. Submit the training job

```bash
qsub nscc/train.pbs
qstat -u $USER
tail -f logs/medvlm-r1-train.out
```

Before submitting, fill in the `TODO`s at the top of `nscc/train.pbs`: GPU count, walltime (no training-time figures are published anywhere for this paper — 8h is a generous starting guess, tighten once you've seen one epoch's pace), and your W&B entity (or switch `--report_to` to `none`).

## 5. Evaluate

`test_script.sh` (unmodified from upstream) runs eval against the already-committed `MRI_CT_XRAY_300each_dataset.json`. Same pattern: fill in its placeholders, run from a compute node.
