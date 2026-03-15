# Bartzialis 

import rclpy
from rclpy.node import Node
import pygame
from std_msgs.msg import Bool, Float32

#Open pygame window
WIN = pygame.display.set_mode((900, 100))
pygame.display.set_caption("keys")
FPS = 60

#Teleoperate the vehicle from this pygame window 
class Teleop(Node):
    def __init__(self):
        super().__init__('key_teleop_node')
        pygame.init()

        self.publisher = self.create_publisher(Bool, 'start_game', 10)

        self.throttle_pub = self.create_publisher(Float32, 'topic_throttle', 10)
        self.steering_pub = self.create_publisher(Float32, 'topic_steering', 10)
        self.respawn_pub = self.create_publisher(Bool, 'topic_respawn', 10)
        
        self.helper = True
        self.clock = pygame.time.Clock()

        self.msg_a = Float32()
        self.msg_b = Float32()
        self.msg_c = Float32()
        self.msg_d = Float32()
        self.msg_e = Float32()
        self.max_acceleration = 1.0
        self.acceleration = 0.0
        self.steerleft = 0.0
        self.max_steerleft = -1.0
        self.steerright = 0
        self.max_steerright = 1.0
        self.braking = 0.0
        self.max_braking = 1.0

        self.Run()

    #Start the Game
    def publish_callback(self):
            msg = Bool()
            msg.data = True
            self.publisher.publish(msg)
    #Throttle teleop
    def Throttle(self):
        self.acceleration = min(self.acceleration + 0.1, self.max_acceleration)
        self.msg_a.data = self.acceleration
        self.braking = float(max(self.braking - self.acceleration, 0))
        self.throttle_pub.publish(self.msg_a)

    #Steer left teleop    
    def SteerLeft(self):
        self.steerleft = float(max(self.steerleft - 0.1, self.max_steerleft))
        self.steerright = float(max(self.steerright + self.steerleft, 0))
        self.msg_b.data = self.steerleft
        self.steering_pub.publish(self.msg_b)

    #Steer right teleop
    def SteerRight(self):
        self.steerright = float(min(self.steerright + 0.1, self.max_steerright))
        self.steerleft = float(min(self.steerleft + self.steerright, 0))
        self.msg_c.data = self.steerright
        self.steering_pub.publish(self.msg_c)

    #Respawn teleop
    def Respawn(self):
        msg = Bool()
        msg.data = True
        self.respawn_pub.publish(msg)

    #Keybinds to teleop
    def TeleopKeys(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.SteerLeft()
            print(self.steerleft)
        else:
            self.steerleft = 0.0
        if keys[pygame.K_d]:
            self.SteerRight()
            print(self.steerright)
        else:
            self.steerright = 0.0
        if keys[pygame.K_w]:
            self.Throttle()
            print(self.acceleration)
        else:
            self.acceleration = 0.0
        if keys[pygame.K_r]:
            self.Respawn()
            self.steerleft = 0.0
            self.acceleration = 0.0

    #Run the commands above and the while loop in order to run the game
    def Run(self):
        while self.helper:
            self.clock.tick(FPS)

            self.publish_callback()

            self.TeleopKeys()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()


def main(args=None):
    rclpy.init(args=args)

    teleop = Teleop()
    rclpy.spin(teleop)

    teleop.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
