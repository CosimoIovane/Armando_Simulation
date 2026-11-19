#include "rclcpp/rclcpp.hpp"

#include <string>

#include "aruco_msgs/msg/marker_array.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

class ArucoTargetAdapterNode : public rclcpp::Node
{
public:
  ArucoTargetAdapterNode()
  : Node("aruco_target_adapter_node")
  {
    target_id_ = this->declare_parameter<int>("target_id", 0);
    target_x_ = this->declare_parameter<double>("target_x", 0.2);
    target_y_ = this->declare_parameter<double>("target_y", 0.0);
    target_z_ = this->declare_parameter<double>("target_z", 0.3);
    markers_topic_ = this->declare_parameter<std::string>("markers_topic", "/marker_publisher/markers");
    target_pose_topic_ = this->declare_parameter<std::string>("target_pose_topic", "/target_pose");
    target_frame_id_ = this->declare_parameter<std::string>("target_frame_id", "base_link");

    target_pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>(
      target_pose_topic_, 10);

    markers_sub_ = this->create_subscription<aruco_msgs::msg::MarkerArray>(
      markers_topic_, 10,
      std::bind(&ArucoTargetAdapterNode::markers_callback, this, std::placeholders::_1));

    RCLCPP_INFO(
      this->get_logger(),
      "Adapter pronto | target_id: %d | target: (%.2f, %.2f, %.2f) in %s | pub: %s",
      target_id_, target_x_, target_y_, target_z_, target_frame_id_.c_str(),
      target_pose_topic_.c_str());
  }

private:
  void markers_callback(const aruco_msgs::msg::MarkerArray::SharedPtr msg)
  {
    target_id_ = this->get_parameter("target_id").as_int();
    target_x_ = this->get_parameter("target_x").as_double();
    target_y_ = this->get_parameter("target_y").as_double();
    target_z_ = this->get_parameter("target_z").as_double();

    for (const auto & marker : msg->markers) {
      if (marker.id != target_id_) {
        continue;
      }

      geometry_msgs::msg::PoseStamped out_msg;
      out_msg.header.frame_id = target_frame_id_;
      out_msg.header.stamp = this->now();

      out_msg.pose.position.x = target_x_;
      out_msg.pose.position.y = target_y_;
      out_msg.pose.position.z = target_z_;

      out_msg.pose.orientation.x = 0.0;
      out_msg.pose.orientation.y = 0.0;
      out_msg.pose.orientation.z = 0.0;
      out_msg.pose.orientation.w = 1.0;

      target_pose_pub_->publish(out_msg);
      return;
    }
  }

  int target_id_{0};
  double target_x_{0.2};
  double target_y_{0.0};
  double target_z_{0.3};
  std::string markers_topic_;
  std::string target_pose_topic_;
  std::string target_frame_id_;

  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr target_pose_pub_;
  rclcpp::Subscription<aruco_msgs::msg::MarkerArray>::SharedPtr markers_sub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ArucoTargetAdapterNode>());
  rclcpp::shutdown();
  return 0;
}
