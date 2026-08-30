// practice.cpp : 3주차 Appendix B3 슬라이드의 실물.
// week03의 talker(파이썬)와 같은 구조의 노드를 C++로 쓴 것 —
// 구조(상속·타이머·콜백)는 동일하고 문법만 다릅니다.
#include <chrono>
#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"                // ROS 2 C++ 클라이언트 라이브러리
#include "std_msgs/msg/string.hpp"          // 메시지 헤더 — package.xml의 depend에 선언!

class Practice : public rclcpp::Node {      // Node 상속 — 파이썬과 같은 구조 (3주차 19쪽)
public:
  Practice() : Node("practice") {           // 노드 이름 등록
    pub_ = create_publisher<std_msgs::msg::String>("chat", 10);   // 토픽·QoS (3주차 29쪽)
    timer_ = create_wall_timer(std::chrono::seconds(1),           // 1초마다 콜백
                               std::bind(&Practice::cb, this));
  }

private:
  void cb() {                               // 타이머 콜백
    auto msg = std_msgs::msg::String();
    msg.data = "hello";
    pub_->publish(msg);                     // 발행
    RCLCPP_INFO(get_logger(), "%s", msg.data.c_str());   // print 대신 로그 (3주차 28쪽)
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv) {          // ★ add_executable이 가리키는 main
  rclcpp::init(argc, argv);                 // ROS 통신 시작
  rclcpp::spin(std::make_shared<Practice>());   // 콜백 대기 루프
  rclcpp::shutdown();
  return 0;
}
