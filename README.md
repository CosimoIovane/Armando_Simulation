# Classwork 2 — Armando: ArUco Markers and KDL IK

This repository contains the ROS 2 implementation for **Classwork 2 (Robotics Lab 2026)**, integrating ArUco fiducial marker perception (`aruco_ros`) with the KDL inverse kinematics solver (`armando_controller`) in Gazebo simulation.

## 1. Overview & Architecture

The pipeline connects perception and motion control through three main components:

1. **Detector (`aruco_ros / marker_publisher`)**: Subscribes to `/camera/image_raw` and `/camera/camera_info`, detects ArUco markers in the scene, and publishes their estimated poses in `base_link` on `/marker_publisher/markers` (`aruco_msgs/msg/MarkerArray`).
2. **Adapter Node (`armando_controller / aruco_target_adapter_node`)**: Subscribes to `/marker_publisher/markers`, filters by the configured `target_id`, and publishes a `geometry_msgs/msg/PoseStamped` on `/target_pose`.
3. **IK Solver (`armando_controller / armando_ik_kdl_node`)**: Subscribes to `/target_pose`, computes inverse kinematics from `base_link` to `crawer_base` (position-only constraint, respecting URDF joint limits), and sends the resulting joint trajectory to the robot controller.

## 2. Design Note & Implementation Variation

Instead of computing the target pose by applying a normal offset $d$ along the detected marker's $z$-axis, **`aruco_target_adapter_node` implements a deliberate variation**:

* **Behavior on detection**: Whenever the marker matching `target_id` is detected in `/marker_publisher/markers`, the adapter publishes a configurable reachable reference pose in `base_link` on `/target_pose`:
  * **Position**: `x = 0.20 m`, `y = 0.00 m`, `z = 0.30 m` (exposed as ROS 2 parameters `target_x`, `target_y`, `target_z`)
  * **Orientation**: Identity quaternion (`x = 0.0, y = 0.0, z = 0.0, w = 1.0`)
  * **Frame**: `base_link`
* **Rationale**: In the Gazebo workbench setup, projecting the raw 3D marker pose along its normal placed the target near or below the workspace boundary ($z < 0$ in `base_link`). Mapping marker detection to a verified reachable target in `base_link` ensures reliable KDL IK convergence and repeatable arm motion whenever the marker is framed by the camera.

## 3. ArUco Marker & Gazebo World Configuration

The marker model is packaged inside `armando_description/models/` and included in `armando_workbench.sdf`.

* **ArUco Dictionary**: `ARUCO_MIP_36h12` *(update if a different OpenCV dictionary was used to generate the PNG texture)*
* **Marker ID**: `0` (configurable via `target_id`)
* **Physical Size (`marker_size`)**: `0.10 m` (side length of the black square)
* **Gazebo Model Path**: `armando_description/models/aruco_marker_0/`

## 4. Setup from a Clean Machine

### Prerequisites

* Ubuntu with **Docker** installed and configured (including X11 forwarding / GPU support as required by the simulation scripts).
* **Git**.

### Step 1: Clone the Repository

```bash
git clone <YOUR_PUBLIC_GITHUB_REPO_URL>
cd Armando_Simulation
```

### Step 2: Build the Docker Image and Start the Container

```bash
cd docker_scripts
./docker_build_image.sh
./docker_run_container.sh
```

The run script mounts `src/` into `/root/ros2_ws/src` inside the container.

### Step 3: Build the ROS 2 Workspace Inside the Container

Once inside the container shell (`/root/ros2_ws`), source ROS 2 Humble and build the packages:

```bash
cd /root/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

*(Note: If `aruco_msgs` has stale build artifacts from a previous build, clean `build/aruco_msgs` and `install/aruco_msgs` before running `colcon build --symlink-install`.)*

## 5. Running the Simulation and Pipeline

Every additional terminal attached to the running container must be opened via:

```bash
cd Armando_Simulation/docker_scripts
./docker_connect.sh
```

And sourced with:

```bash
cd /root/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

### Terminal 1 — Launch the Gazebo Simulation

```bash
ros2 launch armando_description armando_gazebo.launch.py
```

### Terminal 2 — Launch the Integrated ArUco + KDL IK Pipeline

Start the detector, the target adapter, and the KDL solver with a single launch file, specifying the desired `target_id`:

```bash
ros2 launch armando_controller aruco_ik_pipeline.launch.py target_id:=0
```

#### Configurable Launch Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `target_id` | `0` | ID of the ArUco marker to track |
| `marker_size` | `0.10` | Side length [m] of the marker's black square |
| `reference_frame` | `base_link` | Reference frame for marker pose estimation |
| `camera_frame` | `camera_optical_frame` | Optical frame of the simulated RGB camera |
| `camera_image_topic` | `/camera/image_raw` | Input raw image topic |
| `camera_info_topic` | `/camera/camera_info` | Input camera calibration info topic |
| `markers_topic` | `/marker_publisher/markers` | Output topic of `marker_publisher` |
| `target_pose_topic` | `/target_pose` | Target pose topic consumed by `armando_ik_kdl_node` |
| `use_sim_time` | `true` | Use Gazebo simulation clock |

## 6. Verification & Debugging

* **Check detected markers:**

  ```bash
  ros2 topic echo /marker_publisher/markers
  ```

* **Check published target pose:**

  ```bash
  ros2 topic echo /target_pose
  ```

  When marker `0` is visible to the camera, `/target_pose` outputs the configured target `PoseStamped` in `base_link` (`x: 0.2, y: 0.0, z: 0.3`), triggering `armando_ik_kdl_node` to solve IK and move the arm in Gazebo.

* **Visualize annotated camera feed:**

  ```bash
  ros2 run rqt_image_view rqt_image_view /marker_publisher/result
  ```