#!/usr/bin/env python3
"""
extract_tracks_kalman.py
Robust 2D ball tracker: HSV + motion mask + simple Kalman filter + interpolation.
Writes raw_tracks.json by default.
"""
import cv2
import numpy as np
import json
import argparse
import os
import sys

class Kalman2D:
    def __init__(self, dt=1.0, process_var=1e-3, meas_var=25.0):
        # State: [x, y, vx, vy]
        self.dt = dt
        self.A = np.array([[1,0,dt,0],
                           [0,1,0,dt],
                           [0,0,1,0],
                           [0,0,0,1]], dtype=float)
        self.H = np.array([[1,0,0,0],
                           [0,1,0,0]], dtype=float)
        self.P = np.eye(4) * 500.0
        self.x = np.zeros((4,1))
        self.Q = np.eye(4) * process_var
        self.R = np.eye(2) * meas_var

    def predict(self):
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q
        return self.x[:2].ravel()

    def update(self, meas):
        z = np.array(meas, dtype=float).reshape(2,1)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        y = z - (self.H @ self.x)
        self.x = self.x + K @ y
        I = np.eye(self.P.shape[0])
        self.P = (I - K @ self.H) @ self.P
        return self.x[:2].ravel()

def track_ball(video_path, resize=(960,540), max_frames=None,
               hsv_lower=(0,50,50), hsv_upper=(30,255,255)):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    max_frames = frame_count if max_frames is None else min(frame_count, max_frames)

    kalman = Kalman2D(dt=1.0, process_var=1e-3, meas_var=50.0)
    fgbg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50, detectShadows=False)

    detections = []
    last_valid = None
    kernel = np.ones((3,3), np.uint8)

    for i in range(max_frames):
        ret, frame = cap.read()
        if not ret:
            break

        fr = cv2.resize(frame, resize)
        hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        found = False
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > 20:
                (x,y), r = cv2.minEnclosingCircle(c)
                meas = (float(x), float(y))
                if last_valid is None:
                    kalman.x[:2,0] = np.array(meas)
                pred = kalman.update(meas)
                detections.append({"frame": i, "x": float(pred[0]), "y": float(pred[1])})
                last_valid = (i, meas)
                found = True

        if not found:
            # motion mask fallback
            fg = fgbg.apply(fr)
            fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=1)
            cnts2, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best = None
            best_area = 0
            for c in cnts2:
                area = cv2.contourArea(c)
                if 20 < area < 0.06 * (resize[0]*resize[1]) and area > best_area:
                    x,y,w,h = cv2.boundingRect(c)
                    best_area = area
                    best = (int(x + w/2), int(y + h/2))
            if best is not None:
                pred = kalman.update(best)
                detections.append({"frame": i, "x": float(pred[0]), "y": float(pred[1])})
                last_valid = (i, best)
            else:
                # no detection: append None and advance Kalman
                kalman.predict()
                detections.append({"frame": i, "x": None, "y": None})

    cap.release()
    return detections

def interpolate_missing(detections):
    frames = [d["frame"] for d in detections]
    xs = [d["x"] for d in detections]
    ys = [d["y"] for d in detections]

    def interp(vals):
        arr = np.array([v if v is not None else np.nan for v in vals], dtype=float)
        n = len(arr)
        idx = np.arange(n)
        mask = ~np.isnan(arr)
        if mask.sum() < 2:
            return arr.tolist()
        filled = np.interp(idx, idx[mask], arr[mask])
        return filled.tolist()

    xs_f = interp(xs)
    ys_f = interp(ys)

    out = []
    for i, f in enumerate(detections):
        out.append({"frame": int(f["frame"]), "x": float(xs_f[i]), "y": float(ys_f[i])})
    return out

def save_tracks(tracks, out_json="raw_tracks.json"):
    with open(out_json, "w") as f:
        json.dump(tracks, f, indent=2)
    print("Saved tracks to", out_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track ball and save raw tracks (2D).")
    parser.add_argument("video", nargs='?', default="/mnt/data/lbw.mp4", help="Input video path")
    parser.add_argument("--out", default="raw_tracks.json", help="Output JSON")
    parser.add_argument("--resize", default="960x540", help="Resize WxH")
    parser.add_argument("--maxframes", type=int, default=None, help="Max frames to process")
    args = parser.parse_args()

    w,h = map(int, args.resize.split("x"))
    print("Tracking video:", args.video)
    tracks = track_ball(args.video, resize=(w,h), max_frames=args.maxframes)
    tracks_interp = interpolate_missing(tracks)
    save_tracks(tracks_interp, args.out)
