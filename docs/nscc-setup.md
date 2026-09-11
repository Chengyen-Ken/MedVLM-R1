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

## 3. Dataset — hold here before downloading

The repo's own README says to download `FreedomIntelligence/PubMedVision` (~59.5GB). But the actual training code (`grpo.py`, for `DATASET=Huatuo`) loads sample *metadata* from a **different** dataset, `FreedomIntelligence/Medical_Multimodal_Evaluation_Data` (test split, filtered to the MR/CT/X-Ray subsets, 500 samples each), and for each sample resolves the image file as:

```python
image_path = os.path.join(base_image_path, example["image"][0])
```

`base_image_path` is `--dataset_name` — a local directory you populate, not a HF dataset id. Whether PubMedVision's extracted files land at paths matching `example["image"][0]` is still being verified. **Don't bulk-download 59.5GB until this is confirmed** — the exact steps will be added here once it is.

## 4. Submit the training job

```bash
qsub nscc/train.pbs
qstat -u $USER
tail -f logs/medvlm-r1-train.out
```

Before submitting, fill in the `TODO`s at the top of `nscc/train.pbs`: GPU count, walltime (no training-time figures are published anywhere for this paper — 8h is a generous starting guess, tighten once you've seen one epoch's pace), and your W&B entity (or switch `--report_to` to `none`).

## 5. Evaluate

`test_script.sh` (unmodified from upstream) runs eval against the already-committed `MRI_CT_XRAY_300each_dataset.json`. Same pattern: fill in its placeholders, run from a compute node.
