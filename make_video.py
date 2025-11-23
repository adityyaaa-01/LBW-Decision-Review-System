#!/usr/bin/env python3
import cv2
import os
import argparse
from tqdm import tqdm

def is_image(filename):
    return filename.lower().endswith((".png", ".jpg", ".jpeg"))

def create_video(frames_dir, output_file, fps=30, interpolate=False):
    if not os.path.exists(frames_dir):
        print(f"ERROR: Frames directory '{frames_dir}' does not exist.")
        return

    frames = sorted([f for f in os.listdir(frames_dir) if is_image(f)])
    if not frames:
        print("ERROR: No image frames found!")
        return

    first_frame = cv2.imread(os.path.join(frames_dir, frames[0]))
    height, width, _ = first_frame.shape

    ext = output_file.split(".")[-1].lower()
    if ext == "mp4":
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    elif ext == "webm":
        fourcc = cv2.VideoWriter_fourcc(*"VP80")
    else:
        print("ERROR: Unsupported output format. Use .mp4 or .webm")
        return

    writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    print(f"Creating video: {output_file} | FPS: {fps} | Frames: {len(frames)} | Interp: {interpolate}")

    for fn in tqdm(frames, desc="Writing frames"):
        img = cv2.imread(os.path.join(frames_dir, fn))
        if img is None:
            print("Warning: couldn't read", fn)
            continue
        writer.write(img)
        if interpolate:
            # simple duplication interpolation
            writer.write(img)

    writer.release()
    print("Saved:", output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encode frames into video")
    parser.add_argument("--frames", default="frames", help="Frames folder")
    parser.add_argument("--out", default="output.mp4", help="Output file (.mp4 or .webm)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--smooth", action="store_true", help="Duplicate frames for simple smoothing")
    args = parser.parse_args()

    create_video(args.frames, args.out, fps=args.fps, interpolate=args.smooth)
