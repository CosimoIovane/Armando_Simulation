from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    controller_share = FindPackageShare("armando_controller")
    kdl_launch_path = PathJoinSubstitution(
        [controller_share, "launch", "armando_ik_kdl.launch.py"]
    )

    target_id = LaunchConfiguration("target_id")
    offset_distance = LaunchConfiguration("offset_distance")
    marker_size = LaunchConfiguration("marker_size")
    reference_frame = LaunchConfiguration("reference_frame")
    camera_frame = LaunchConfiguration("camera_frame")
    image_is_rectified = LaunchConfiguration("image_is_rectified")
    camera_image_topic = LaunchConfiguration("camera_image_topic")
    camera_info_topic = LaunchConfiguration("camera_info_topic")
    markers_topic = LaunchConfiguration("markers_topic")
    target_pose_topic = LaunchConfiguration("target_pose_topic")
    use_sim_time = LaunchConfiguration("use_sim_time")

    detector_node = Node(
        package="aruco_ros",
        executable="marker_publisher",
        name="marker_publisher",
        output="screen",
        parameters=[
            {
                "marker_size": marker_size,
                "reference_frame": reference_frame,
                "camera_frame": camera_frame,
                "image_is_rectified": image_is_rectified,
                "use_sim_time": use_sim_time,
            }
        ],
        remappings=[
            ("/camera_info", camera_info_topic),
            ("/image", camera_image_topic),
        ],
    )

    adapter_node = Node(
        package="armando_controller",
        executable="aruco_target_adapter_node",
        name="aruco_target_adapter_node",
        output="screen",
        parameters=[
            {
                "target_id": target_id,
                "offset_distance": offset_distance,
                "markers_topic": markers_topic,
                "target_pose_topic": target_pose_topic,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    kdl_solver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(kdl_launch_path),
        launch_arguments={
            "target_pose_topic": target_pose_topic,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("target_id", default_value="0"),
            DeclareLaunchArgument("offset_distance", default_value="0.15"),
            DeclareLaunchArgument("marker_size", default_value="0.10"),
            DeclareLaunchArgument("reference_frame", default_value="base_link"),
            DeclareLaunchArgument("camera_frame", default_value="camera_optical_frame"),
            DeclareLaunchArgument("image_is_rectified", default_value="true"),
            DeclareLaunchArgument("camera_image_topic", default_value="/camera/image_raw"),
            DeclareLaunchArgument("camera_info_topic", default_value="/camera/camera_info"),
            DeclareLaunchArgument("markers_topic", default_value="/marker_publisher/markers"),
            DeclareLaunchArgument("target_pose_topic", default_value="/target_pose"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            detector_node,
            adapter_node,
            kdl_solver_launch,
        ]
    )
