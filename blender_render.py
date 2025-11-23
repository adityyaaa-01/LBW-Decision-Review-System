import bpy
import json
import sys
import os
import math

# -------------------------------------------
# Parse arguments (Blender gives unknown args first)
# -------------------------------------------
argv = sys.argv
argv = argv[argv.index("--") + 1:]

tracks_path = argv[0]
output_path = argv[1] if len(argv) > 1 else "animation.mp4"

# Output frames folder
frames_dir = os.path.join(os.path.dirname(bpy.data.filepath), "frames")
if not os.path.exists(frames_dir):
    os.makedirs(frames_dir)

# -------------------------------------------
# Reset scene
# -------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

# -------------------------------------------
# Create green ground + brown pitch
# -------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=50)
ground = bpy.context.active_object
mat_ground = bpy.data.materials.new("GroundMat")
mat_ground.diffuse_color = (0.05, 0.3, 0.05, 1)   # green grass tone
ground.data.materials.append(mat_ground)

# Pitch strip
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, -10, 0.01))
pitch = bpy.context.active_object
pitch.scale[1] = 10   # long pitch
mat_pitch = bpy.data.materials.new("PitchMat")
mat_pitch.diffuse_color = (0.45, 0.35, 0.25, 1)  # brownish pitch
pitch.data.materials.append(mat_pitch)

# -------------------------------------------
# Create stumps
# -------------------------------------------
def create_stump(x_offset):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.1, location=(x_offset, 0, 0.55))
    stump = bpy.context.active_object
    mat = bpy.data.materials.new("StumpMat")
    mat.diffuse_color = (0.9, 0.9, 0.9, 1)   # off-white
    stump.data.materials.append(mat)
    return stump

create_stump(-0.15)
create_stump(0.0)
create_stump(0.15)

# -------------------------------------------
# Create ball
# -------------------------------------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 15, 1))
ball = bpy.context.active_object
mat_ball = bpy.data.materials.new("BallMat")
mat_ball.diffuse_color = (0.8, 0.1, 0.1, 1)
ball.data.materials.append(mat_ball)

# -------------------------------------------
# Load trajectory
# -------------------------------------------
with open(tracks_path, "r") as f:
    tracks = json.load(f)

# -------------------------------------------
# Animate ball
# -------------------------------------------
for p in tracks:
    frame = p["frame"]
    ball.location = (p["x"], p["y"], p["z"])
    ball.keyframe_insert(data_path="location", frame=frame)

# -------------------------------------------
# Camera setup
# -------------------------------------------
bpy.ops.object.camera_add(location=(4, -15, 5), rotation=(math.radians(75), 0, math.radians(30)))
cam = bpy.context.active_object
bpy.context.scene.camera = cam

# -------------------------------------------
# Lighting
# -------------------------------------------
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 5

# -------------------------------------------
# Render settings
# -------------------------------------------
scene = bpy.context.scene
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(frames_dir, "frame_")
scene.render.fps = 30
scene.render.engine = "BLENDER_EEVEE"

# -------------------------------------------
# Render animation
# -------------------------------------------
scene.frame_start = tracks[0]["frame"]
scene.frame_end = tracks[-1]["frame"]
bpy.ops.render.render(animation=True)
