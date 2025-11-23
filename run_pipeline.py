#!/usr/bin/env python3
"""
run_pipeline.py
Orchestrates:
1) extract_tracks_kalman.py -> raw_tracks.json
2) physics_reconstruct.py -> tracks.json
3) Blender headless call to render frames (blender_render.py)
4) make_video.py -> final_output.mp4
"""
import subprocess
import sys
import os

# Change this if Blender is installed elsewhere
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

# Input video (the uploaded file path used earlier)
VIDEO_IN = r"/mnt/data/lbw.mp4"

RAW_TRACKS = "raw_tracks.json"
TRACKS_3D = "tracks.json"
FRAMES_DIR = "frames"
OUTPUT_VIDEO = "final_output.mp4"

def run(cmd, env=None):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, env=env)

def main():
    cwd = os.getcwd()
    print("Working dir:", cwd)

    # 1) Extract tracks
    print("\n1) Extracting 2D tracks...")
    run([sys.executable, "extract_tracks_kalman.py", VIDEO_IN, "--out", RAW_TRACKS, "--resize", "960x540"])

    # 2) Physics reconstruct
    print("\n2) Reconstructing 3D trajectory...")
    run([sys.executable, "physics_reconstruct.py", "--in", RAW_TRACKS, "--out", TRACKS_3D, "--imgsize", "960x540", "--fps", "30"])

    # 3) Render in Blender
    print("\n3) Rendering frames in Blender (headless)...")
    if not os.path.exists(BLENDER_EXE):
        print("ERROR: Blender executable not found at:", BLENDER_EXE)
        print("Please set BLENDER_EXE in run_pipeline.py to your blender.exe path and re-run.")
        return

    # Ensure frames folder exists (Blender will fill it)
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR, exist_ok=True)

    run([BLENDER_EXE, "--background", "--python", "blender_render.py", "--", TRACKS_3D, OUTPUT_VIDEO])

    # 4) Encode final video using system Python (make_video.py)
    print("\n4) Encoding final video from frames...")
    run([sys.executable, "make_video.py", "--frames", FRAMES_DIR, "--out", OUTPUT_VIDEO, "--fps", "30"])

    print("\nPipeline finished. Output:", OUTPUT_VIDEO)

if __name__ == "__main__":
    main()
