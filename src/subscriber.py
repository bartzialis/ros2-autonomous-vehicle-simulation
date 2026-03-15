# Bartzialis

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32

#Callbacks for the information being published from the game about the vehicle
class GameSubscriber(Node):
    def __init__(self):
        super().__init__('Game_subscriber')
        self.msg1 = 0
        self.msg2 = 0
        self.msg3 = 0
        self.msg4 = 0
        self.msg5 = "none"

        self.subscription_x = self.create_subscription(Int32, 'topic_x', self.listener_callback_x, 10)
        self.subscription_y = self.create_subscription(Int32, 'topic_y', self.listener_callback_y, 10)
        self.subscription_lap = self.create_subscription(Int32, 'topic_lap', self.listener_callback_lap, 10)
        self.subscription_vel = self.create_subscription(Int32, 'topic_vel', self.listener_callback_vel, 10)
        self.subscription_gear = self.create_subscription(String, 'topic_gear', self.listener_callback_gear, 10)

    def listener_callback_x(self, msg):
        self.msg1 = msg
        self.get_logger().info('x: "%d"' % msg.data)
    def listener_callback_y(self, msg2):
        self.msg2 = msg2
        self.get_logger().info('y: "%d"' % msg2.data)
    def listener_callback_lap(self, msg3):
        self.msg3 = msg3
        self.get_logger().info('lap: "%d"' % msg3.data)
    def listener_callback_vel(self, msg4):
        self.msg4 = msg4
        self.get_logger().info('velocity: "%d"' % msg4.data)
    def listener_callback_gear(self, msg5):
        self.msg5 = msg5
        self.get_logger().info('gear: "%s"' % msg5.data)
        print("\n")
        

def main(args=None):
    rclpy.init(args=args)

    game_subscriber = GameSubscriber()

    rclpy.spin(game_subscriber)
    game_subscriber.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
