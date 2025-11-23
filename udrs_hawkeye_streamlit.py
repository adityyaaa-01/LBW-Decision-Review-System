import streamlit as st
import subprocess
import sys
import os
import json
import tempfile
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="UDRS Analysis", layout="wide")

st.title("UDRS — HawkEye Style Video Analysis (Updated Pipeline)")

# Paths
EXTRACT_SCRIPT = "extract_tracks_kalman.py"
PHYSICS_SCRIPT = "physics_reconstruct.py"
RAW_TRACKS = "raw_tracks.json"
TRACKS_OUT = "tracks.json"

# Blender command example
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
BLENDER_CMD = f'"{BLENDER_EXE}" --background --python blender_render.py -- {TRACKS_OUT} final_output.mp4'

# Upload Section
st.header("1) Upload Cricket Video")
uploaded = st.file_uploader("Upload your cricket video", type=["mp4", "mov", "avi"])

video_path = None
temp_file = None

if uploaded:
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp.write(uploaded.read())
    temp.flush()
    temp.close()
    temp_file = temp.name
    video_path = temp_file
    st.success("Video uploaded successfully!")
    st.video(video_path)
else:
    st.info("Please upload a video to continue.")
    st.stop()

# Analysis Section
st.header("2) Analyze Video")

if st.button("Start Analysis"):
    if not video_path:
        st.error("No video selected.")
        st.stop()

    # Run tracker
    with st.spinner("Running 2D Tracker..."):
        cmd = [sys.executable, EXTRACT_SCRIPT, video_path, "--out", RAW_TRACKS, "--resize", "960x540"]
        subprocess.run(cmd, check=True)

    # Run physics reconstruction
    with st.spinner("Reconstructing 3D Trajectory..."):
        cmd2 = [sys.executable, PHYSICS_SCRIPT, "--in", RAW_TRACKS, "--out", TRACKS_OUT, "--imgsize", "960x540", "--fps", "30"]
        subprocess.run(cmd2, check=True)

    st.success("Analysis complete! 3D trajectory generated.")

# Load and Visualize Tracks
if os.path.exists(TRACKS_OUT):
    st.header("3) Trajectory Preview & Decision")

    with open(TRACKS_OUT, "r") as f:
        tracks = json.load(f)

    if len(tracks) == 0:
        st.error("tracks.json is empty — tracking failed.")
        st.stop()

    # Convert to arrays
    xs = np.array([p["x"] for p in tracks])
    ys = np.array([p["y"] for p in tracks])
    zs = np.array([p["z"] for p in tracks])

    # Plot trajectory
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    ax[0].plot(xs, ys, "-o", markersize=3)
    ax[0].invert_yaxis()
    ax[0].set_title("2D Flight Path (Top View)")
    ax[0].set_xlabel("X (m)")
    ax[0].set_ylabel("Y (m forward)")

    ax[1].plot(ys, zs, "-o", markersize=3)
    ax[1].set_title("Height vs Forward Distance")
    ax[1].set_xlabel("Y (m forward)")
    ax[1].set_ylabel("Z (height m)")

    st.pyplot(fig)

    # Prediction
    stump_hits = [p for p in tracks if p["y"] <= 0]
    if stump_hits:
        hit = stump_hits[0]
        if abs(hit["x"]) <= 0.10:
            st.error("🟥 Prediction: OUT — Ball projected to hit stumps")
            st.write(f"x={hit['x']:.2f} m, y={hit['y']:.2f} m")
        else:
            st.success("🟦 Prediction: NOT OUT — Ball missing stumps")
            st.write(f"x offset too large (x={hit['x']:.2f})")
    else:
        st.info("Ball trajectory does not reach stumps.")

    # Show sample rows
    st.subheader("Sample Track Points")
    for i in [0, len(tracks)//2, len(tracks)-1]:
        p = tracks[i]
        st.write(f"Frame {p['frame']} → x={p['x']:.2f}, y={p['y']:.2f}, z={p['z']:.2f}")

    st.markdown("---")

    # Download JSON
    with open(TRACKS_OUT, "r") as f:
        st.download_button("Download tracks.json", f.read(), file_name="tracks.json")

    # Blender Instructions
    st.header("4) Generate Blender Animation")
    st.write("Copy and run this command in CMD:")

    st.code(BLENDER_CMD)

    st.write("After Blender finishes rendering PNG frames into /frames, run:")
    st.code("python make_video.py --frames frames --out final_output.mp4 --fps 30")

# Cleanup
if temp_file:
    try: os.remove(temp_file)
    except: pass

st.markdown("---")
st.write("UDRS Streamlit App — Updated to match new fast tracking + physics pipeline.")
