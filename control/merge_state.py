import os
import sys
import json
import glob
import shutil

def merge_artifacts(artifacts_dir: str, state_dir: str = "state"):
    print(f"Merging artifacts from {artifacts_dir} into {state_dir}...")
    if not os.path.exists(artifacts_dir):
        print(f"No artifacts directory found at {artifacts_dir}. Skipping.")
        return

    # Find all channel state folders in artifacts
    for item in os.listdir(artifacts_dir):
        src_path = os.path.join(artifacts_dir, item)
        if os.path.isdir(src_path):
            channel_name = item.replace("state-", "")
            target_path = os.path.join(state_dir, channel_name)
            os.makedirs(target_path, exist_ok=True)
            for f in glob.glob(os.path.join(src_path, "*")):
                fname = os.path.basename(f)
                dest = os.path.join(target_path, fname)
                shutil.copy2(f, dest)
                print(f"Copied {fname} -> {target_path}")

if __name__ == "__main__":
    dir_to_merge = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
    merge_artifacts(dir_to_merge)
