#!/usr/bin/env python3
"""
physics_reconstruct.py  (Option A — Straight-line forward extrapolation)

Usage:
    python physics_reconstruct.py --in raw_tracks.json --out tracks.json --imgsize 960x540 --fps 30

Input:
    raw_tracks.json  (list of {"frame": int, "x": float, "y": float})
      - x,y are image-space coordinates (same as produced by extract_tracks_kalman.py)

Output:
    tracks.json  (list of {"frame": int, "x": float, "y": float, "z": float})
      - x: lateral meters (-~1.5..1.5)
      - y: forward meters (stumps at y=0)
      - z: height in meters (plausible estimate)
"""
import json
import numpy as np
import argparse
import os
import math

def straight_line_reconstruct(raw_json="raw_tracks.json", out_json="tracks.json",
                              image_size=(960,540), pitch_length_m=20.12, fps=30.0,
                              min_forward_speed=0.5, max_extrap_seconds=4.0):
    if not os.path.exists(raw_json):
        raise FileNotFoundError(f"Input file not found: {raw_json}")

    with open(raw_json, "r") as f:
        raw = json.load(f)

    if not raw:
        raise ValueError("raw_tracks.json is empty")

    # Extract arrays
    frames = np.array([int(p["frame"]) for p in raw], dtype=int)
    xs_img = np.array([float(p["x"]) for p in raw], dtype=float)
    ys_img = np.array([float(p["y"]) for p in raw], dtype=float)

    img_w, img_h = image_size

    # Map image X -> lateral meters (-1.5 .. 1.5)
    x_m = (xs_img / img_w) * 3.0 - 1.5

    # Map image Y -> forward distance along pitch (0 .. pitch_length_m), invert y
    # Note: image y increases downward; mapping makes top -> pitch_length_m, bottom -> 0
    y_m = (1.0 - (ys_img / img_h)) * pitch_length_m

    # Time vector
    t = frames / float(fps)
    dt = 1.0 / float(fps)

    # Robust velocity estimates: use median of gradient over last N valid points
    if len(t) >= 2:
        dy_dt = np.gradient(y_m, t)          # dy/dt (note sign: likely negative if moving toward stumps)
        dx_dt = np.gradient(x_m, t)
    else:
        dy_dt = np.array([0.0])
        dx_dt = np.array([0.0])

    # Forward speed toward stumps should be positive scalar. Since y decreases as it moves forward,
    # we take -dy_dt to get a positive forward speed.
    forward_speeds = -dy_dt
    # filter out negative/noisy values
    forward_speeds = forward_speeds[np.isfinite(forward_speeds)]

    if forward_speeds.size == 0:
        v_forward = min_forward_speed
    else:
        # Use median of last few entries for robustness
        n = min(5, len(forward_speeds))
        v_forward = float(np.median(forward_speeds[-n:]))
        if v_forward <= 0 or not np.isfinite(v_forward):
            v_forward = min_forward_speed

    # Lateral velocity: median of last few dx/dt
    lateral_speeds = dx_dt[np.isfinite(dx_dt)]
    if lateral_speeds.size == 0:
        v_lateral = 0.0
    else:
        v_lateral = float(np.median(lateral_speeds[-n:]))

    # Build an initial z profile: linear from assumed release height to near-ground
    # These are heuristics — Blender will animate based on these z values.
    z0 = 1.6   # typical release height (meters)
    zend = 0.2  # height near impact (meters)
    # Create z for known frames as linear interpolation between z0 and zend across known frames
    if len(t) >= 2:
        z_known = np.linspace(z0, zend, len(t))
    else:
        z_known = np.array([z0])

    # Build output points from the known frames
    out_points = []
    for xi, yi, zi, fi in zip(x_m, y_m, z_known, frames):
        out_points.append({"frame": int(fi), "x": float(xi), "y": float(yi), "z": float(max(0.0, zi))})

    # Extrapolate forward in straight line until y <= 0 (stumps) or safety time limit
    last_frame = int(frames[-1])
    last_x = float(x_m[-1])
    last_y = float(y_m[-1])
    last_z = float(z_known[-1])

    # Safety: if forward speed is tiny, set a reasonable fallback (fast bowling speed ~10 m/s; use smaller)
    if v_forward < min_forward_speed:
        v_forward = min_forward_speed

    max_extra_frames = int(math.ceil(max_extrap_seconds * fps))
    extra = 0

    # Compute z rate to move from last_z -> zend over time_to_stumps (linear)
    time_to_stumps = (last_y / v_forward) if v_forward > 1e-6 else None
    if time_to_stumps and time_to_stumps > 0:
        z_rate = (zend - last_z) / time_to_stumps
    else:
        # fallback small downward rate
        z_rate = (zend - last_z) / max(1.0, max_extrap_seconds)

    # iterate
    while last_y > 0.0 and extra < max_extra_frames:
        last_frame += 1
        last_x = last_x + v_lateral * dt
        last_y = last_y - v_forward * dt   # decrease toward 0
        last_z = last_z + z_rate * dt
        # clamp
        last_y = max(last_y, 0.0)
        last_z = max(last_z, 0.0)
        out_points.append({"frame": int(last_frame), "x": float(last_x), "y": float(last_y), "z": float(last_z)})
        extra += 1

    # If we stopped because of time limit and still last_y > 0, optionally add one final point at stumps
    if last_y > 0.0:
        # force final impact point at y=0 using linear extrapolation
        est_extra_frames_needed = int(math.ceil(last_y / v_forward)) if v_forward > 1e-6 else max_extra_frames
        final_frame = out_points[-1]["frame"] + est_extra_frames_needed
        final_x = out_points[-1]["x"] + v_lateral * (est_extra_frames_needed * dt)
        final_z = max(0.0, zend)
        out_points.append({"frame": int(final_frame), "x": float(final_x), "y": 0.0, "z": float(final_z)})

    # Save to JSON
    with open(out_json, "w") as f:
        json.dump(out_points, f, indent=2)

    print(f"Saved reconstructed 3D tracks to {out_json}")
    print(f"Original frames: {len(frames)}, total output points: {len(out_points)}")
    print(f"Estimated forward speed: {v_forward:.2f} m/s, lateral speed: {v_lateral:.3f} m/s")
    return out_points

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct 3D straight-line trajectory to stumps.")
    parser.add_argument("--in", dest="infile", default="raw_tracks.json", help="Input raw tracks (2D JSON)")
    parser.add_argument("--out", dest="outfile", default="tracks.json", help="Output 3D tracks JSON")
    parser.add_argument("--imgsize", default="960x540", help="Image size used during tracking WxH")
    parser.add_argument("--fps", type=float, default=30.0, help="Video FPS (used for timing)")
    parser.add_argument("--pitchlen", type=float, default=20.12, help="Pitch length in metres")
    args = parser.parse_args()

    w,h = map(int, args.imgsize.split("x"))
    straight_line_reconstruct(raw_json=args.infile, out_json=args.outfile,
                              image_size=(w,h), pitch_length_m=args.pitchlen, fps=args.fps)
