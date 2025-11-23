**LBW Decision Review System**

A complete pipeline that analyzes a cricket delivery video and determines whether the ball would have hit the stumps — similar to the LBW decision review used in professional cricket.

This system processes a normal camera clip and produces:

🎯 Accurate ball tracking

📉 Smoothed trajectory using filtering

📐 3D reconstruction of the ball’s path

⚙️ Physics-based forward projection to estimate final impact

🏏 LBW decision logic (hitting or missing the wickets)

🎥 Full 3D animation in Blender

🎞️ Rendered video output

Everything is processed step-by-step using simple, readable Python scripts.

🌟 Features
**1. Detects and tracks the ball in the video**

The system follows the cricket ball from frame to frame and records its position over time.

**2. Smooths the motion to remove camera noise**

A filtering method is used so the ball path becomes smooth and realistic instead of shaky.

**3. Reconstructs the ball path in 3D space**

The tracked points from the video are converted into real-world coordinates.

**4. Predicts the ball’s future path**

Using basic physics equations (gravity + motion), the system calculates where the ball would continue if it wasn’t interrupted.

**5. Checks whether the ball will hit the stumps**

The system compares the predicted path with the wicket location to decide:

--> Hitting

--> Missing

--> Impact height

**6. Generates a 3D replay using Blender**

Blender is used to create a clean visual animation of the ball trajectory, the pitch, and the wickets.

**7. Renders the final video output**

All Blender frames are combined into a final MP4 video showing the full LBW replay.
