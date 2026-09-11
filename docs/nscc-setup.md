# NSCC Setup (ASPIRE2A)

Runbook for getting this reproduction running on NSCC. Project ID: `csyuchen`, queue `"ai"` (4x A100-40GB per node) — confirm the exact queue name with `qstat -Q` after logging in, NSCC's public docs didn't pin down every queue name beyond `"ai"`.

## 0. Confirmed paths

`$HOME` is `/home/users/ntu/csyuchen`. `$HOME/scratch` exists (works as a `cd` target from home) and is treated as the scratch root — NSCC's `/scratch/$USER` and `/home/project/csyuchen` were both wrong guesses on my part; neither exists, and there's no need to chase the "real" NSCC-wide convention further, since the layout below is a deliberate choice, not a discovered one.

Chosen layout — **scratch is shared across all NSCC projects**, organized by category so future projects reuse the same datasets/envs instead of re-downloading:

```
$HOME/scratch/
├── envs/medvlm-r1/                       this project's conda env
├── datasets/
│   ├── omnimedvqa/                       raw extracted OmniMedVQA — reusable by any future project
│   └── medvlm-r1-huatuo-images/          this project's flattened slice (verify_dataset.py output)
├── hf_cache/                             shared HF_HOME — HF's own cache is content-addressed, safe to share
└── checkpoints/medvlm-r1/<run-name>/     training output, namespaced per project

$HOME/reproduce/MedVLM-R1/                this reproduction's code (persistent, not scratch)
$HOME/project/<future-name>/              where your own original-research projects will go later
```

`nscc/setup_env.sh` and `nscc/train.pbs` already point at these paths (via `$HOME`, not hardcoded) — no editing needed unless you want to change the scheme itself.

## 1. Get the code onto NSCC

```bash
mkdir -p "$HOME/reproduce"
cd "$HOME/reproduce"
git clone https://github.com/Chengyen-Ken/MedVLM-R1.git
cd MedVLM-R1
```

## 2. Build the environment

In scratch, on a compute node — not the login node (flash-attn's build step is heavy and login nodes kill long/CPU-heavy work):

```bash
qsub -I -P csyuchen -q ai -l select=1:ncpus=5:ngpus=1 -l walltime=02:00:00
# once on the compute node:
cd "$HOME/reproduce/MedVLM-R1"
bash nscc/setup_env.sh
```

Creates the conda env at `$HOME/scratch/envs/medvlm-r1` — not under plain `$HOME`, which is too small for a PyTorch + flash-attn stack.

## 3. Dataset

The repo's own README says to download `FreedomIntelligence/PubMedVision` (~59.5GB). **This does not satisfy what the training code actually needs — confirmed, not just suspected:**

- `grpo.py` (for `DATASET=Huatuo`) loads row metadata from a **different** dataset, `FreedomIntelligence/Medical_Multimodal_Evaluation_Data` (test split, filtered to the MR/CT/X-Ray subsets, 500 samples each), and resolves each image at `os.path.join(base_image_path, example["image"][0])`.
- Sampled rows carry `image` filenames like `images/ankle071718.png` and a `dataset` field naming the row's *original* source benchmark (e.g. `OmniMedVQA`, `PMC-VQA_test`) — this dataset is an aggregation over pre-existing medical VQA benchmarks, not something derived from PubMedVision.
- PubMedVision's own files are named `pmc_<n>_<i>.jpg` — different convention, different extension, no overlap with the filenames above.

So the real images need to come from each row's original source benchmark, not PubMedVision. No documentation anywhere (HF dataset cards, the HuatuoGPT-Vision repo, MedVLM-R1's README/issues) reconciles this — looks like an undocumented gap in the upstream repo's reproducibility instructions, not something we're missing.

**Confirmed by full census** (all 1,500 rows the `Huatuo`/`COMBINED` training set actually uses, not a sample): every MR/CT/X-Ray row has `dataset == "OmniMedVQA"`, zero exceptions. The real image source is a single dataset, `foreverbeliever/OmniMedVQA` on Hugging Face — ungated, 10.7GB, 118,010 images from 73 source benchmarks under `Images/<source-dataset-name>/...`. Not the scavenger hunt across many benchmarks it first looked like. Do not download `PubMedVision` for this branch — confirmed unused.

OmniMedVQA itself splits into an "open-access" bucket (images included) and a "restricted-access" bucket (paths only — files require a separate, sometimes gated, request to the original source benchmark, e.g. one candidate source, AIDA, requires a formal application with a PhD requirement). Which bucket applies to MedVLM-R1's specific 1,500 images is **not knowable without downloading** — the HF repo is one monolithic zip with no browsable file listing. This is a real timeline risk against your 2-month deadline if a large chunk turns out gated; the steps below get you a concrete found/missing count in minutes so you know where you stand early rather than discovering it mid-training-run.

```bash
# 1. Download + extract (10.7GB, no partial-download option — it's one zip).
#    Lands under datasets/ at the scratch root, not namespaced to this
#    project, so any future project needing it reuses this same copy.
hf download foreverbeliever/OmniMedVQA --repo-type dataset --local-dir "$HOME/scratch/datasets/omnimedvqa"
cd "$HOME/scratch/datasets/omnimedvqa" && unzip OmniMedVQA.zip

# 2. Check what you actually got against the exact 1,500 filenames grpo.py needs,
#    and materialize a flat images/ dir in the layout grpo.py expects
cd "$HOME/reproduce/MedVLM-R1"
python3 nscc/verify_dataset.py "$HOME/scratch/datasets/omnimedvqa" "$HOME/scratch/datasets/medvlm-r1-huatuo-images"
```

`nscc/verify_dataset.py` (manifest committed alongside it: `nscc/omnimedvqa_manifest.json`, built from a full API census, not a sample) reports found/missing per modality and symlinks every found file into `<output_dir>/images/<name>` — matching how `grpo.py` actually resolves paths (`os.path.join(dataset_name, "images/<name>")`), which doesn't match OmniMedVQA's own nested `Images/<source-dataset>/` layout, hence the symlink step rather than pointing `--dataset_name` straight at the extracted zip.

**If a meaningful chunk comes back missing** (check `missing_images.json`, written next to the symlinked output):
- You can still train with `DATASET_SELECTION=MR` (or whichever single modality has the fewest gaps) instead of `COMBINED`, at the cost of not matching the paper's full training set.
- Chasing down individual restricted-access sources is a real decision against your 2-month deadline — worth deciding early whether it's worth pursuing per-source access requests, or whether a partial/modified reproduction (fewer samples, or documenting the gap) is an acceptable fallback for the reproduction phase, with a fuller dataset pursued later if it matters for the novel-research phase.

Once you're satisfied with the found/missing split, `--dataset_name` in `nscc/train.pbs` already points at `$HOME/scratch/datasets/medvlm-r1-huatuo-images` — matching what the command above just built, no editing needed.

## 4. Submit the training job

```bash
qsub nscc/train.pbs
qstat -u $USER
tail -f logs/medvlm-r1-train.out
```

Before submitting, fill in the `TODO`s at the top of `nscc/train.pbs`: GPU count, walltime (no training-time figures are published anywhere for this paper — 8h is a generous starting guess, tighten once you've seen one epoch's pace), and your W&B entity (or switch `--report_to` to `none`).

## 5. Evaluate

`test_script.sh` (unmodified from upstream) runs eval against the already-committed `MRI_CT_XRAY_300each_dataset.json`. Same pattern: fill in its placeholders, run from a compute node.
