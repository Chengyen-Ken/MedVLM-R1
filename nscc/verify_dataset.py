#!/usr/bin/env python3
"""Verify and materialize MedVLM-R1's Huatuo training images from an extracted OmniMedVQA tree.

grpo.py resolves each training image at os.path.join(base_image_path, "images/<name>").
OmniMedVQA's extracted zip nests files under Images/<source-dataset>/... instead, so this
script finds each needed file by basename anywhere in that tree and symlinks it into a flat
images/ folder matching what grpo.py expects for --dataset_name.

Usage:
  python3 verify_dataset.py <extracted_omnimedvqa_root> <output_dir> [--manifest FILE]

Run after downloading+extracting foreverbeliever/OmniMedVQA (see docs/nscc-setup.md step 3).
<output_dir>/images/ will contain symlinks for every needed file that was found;
<output_dir>/missing_images.json lists what wasn't. Point --dataset_name in train.pbs
at <output_dir> once you're satisfied with the found/missing split.
"""
import argparse
import json
import os
from pathlib import Path


def build_basename_index(root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            index.setdefault(fn, Path(dirpath) / fn)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("extracted_root", type=Path, help="Extracted OmniMedVQA tree (contains Images/<source-dataset>/...)")
    parser.add_argument("output_dir", type=Path, help="Where to materialize a flat images/ dir for --dataset_name")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).parent / "omnimedvqa_manifest.json")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())

    print(f"Indexing {args.extracted_root} ...")
    index = build_basename_index(args.extracted_root)
    print(f"Indexed {len(index)} unique filenames.\n")

    out_images = args.output_dir / "images"
    out_images.mkdir(parents=True, exist_ok=True)

    missing: dict[str, list[str]] = {}
    for modality, paths in manifest.items():
        basenames = [os.path.basename(p) for p in paths]
        miss = []
        for b in basenames:
            src = index.get(b)
            if src is None:
                miss.append(b)
                continue
            dst = out_images / b
            if not dst.exists():
                dst.symlink_to(src.resolve())
        found = len(basenames) - len(miss)
        missing[modality] = miss
        print(f"{modality}: {found}/{len(basenames)} found")

    total_needed = sum(len(v) for v in manifest.values())
    total_missing = sum(len(v) for v in missing.values())
    print(f"\nTotal: {total_needed - total_missing}/{total_needed} found, {total_missing} missing")

    missing_path = args.output_dir / "missing_images.json"
    missing_path.write_text(json.dumps(missing, indent=2))
    print(f"Missing filenames written to {missing_path}")
    print(f"\nIf the found/missing split looks workable, point --dataset_name in train.pbs at: {args.output_dir}")


if __name__ == "__main__":
    main()
