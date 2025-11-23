# LBW Decision Review System

A complete pipeline that analyzes a cricket delivery video and determines whether the ball would have hit the stumps — similar to the LBW decision review used in professional cricket.

The system processes a normal video clip and produces:

- 🎯 Accurate ball tracking  
- 📉 Smoothed trajectory  
- 📐 3D reconstruction  
- ⚙️ Physics-based forward prediction  
- 🏏 LBW decision logic (Hitting or Missing the stumps)  
- 🎥 3D animation in Blender  
- 🎞️ Final rendered video output  

Everything is processed step-by-step using simple Python scripts.

---

## 🌟 Features (Explained Simply)

### 1. Detects and tracks the ball in the video  
The system follows the ball frame-by-frame and records its movement.

### 2. Smooths the motion  
A filtering method is used so the path becomes stable instead of shaky.

### 3. Converts the movement into 3D coordinates  
The tracked points are reconstructed into real-world space.

### 4. Predicts the future path using physics  
Basic motion equations are applied to estimate where the ball would continue travelling.

### 5. Checks if the ball will hit the stumps  
The predicted path is compared with the wicket location to determine the decision.

### 6. Creates a 3D replay using Blender  
Blender is used to animate the delivery, including the ball, pitch, and stumps.

### 7. Produces a final MP4 video  
All animated frames are combined into one smooth video.

---

## 📂 Project Structure

UDRS-Project/
│
├── extract_tracks_kalman.py
├── physics_reconstruct.py
├── blender_render.py
├── make_video.py
├── run_pipeline.py
│
├── input_video.mp4
├── tracks.json
└── frames/

---

## 🛠 Requirements

- Python 3.8+
- Blender 5.0+
- OpenCV  
- NumPy  
- tqdm  

---

## Install Python dependencies:

```bash
pip install opencv-python numpy tqdm
```

🚀 How to Use
1. Extract ball trajectory from the video
```bash
python extract_tracks_kalman.py input_video.mp4 --out raw_tracks.json
```
2. Build the 3D path + predict whether it hits the stumps
```bash
python physics_reconstruct.py --in raw_tracks.json --out tracks.json --fps 30
```
3. Render the 3D animation using Blender
```bash
"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background --python blender_render.py -- tracks.json output.mp4
```
4. Combine the frames into an MP4
```bash
python make_video.py --frames frames --out final_output.mp4
```

---

## 🎥 Output

The system produces:

- A smoothed trajectory
- A prediction (Hitting or Missing)
- A complete 3D replay animation

---

## 📜 License

This project is open-source and free to use for learning and experimentation.
