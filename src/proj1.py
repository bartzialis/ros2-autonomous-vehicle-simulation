# Bartzialis 

import pygame
import math
from rclpy.node import Node
import rclpy
import numpy as np
from extrafunctions import scale_image, rectRotated
from std_msgs.msg import String, Int32, Float32, Bool
from geometry_msgs.msg import TransformStamped, Twist, PoseStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from tf2_ros import TransformBroadcaster
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import PointCloud2, PointField
import std_msgs.msg

#Open pygame window and first setup
FINISH = scale_image(pygame.image.load("finish.png"), 0.8)
FINISH_POS = (136, 250)
BLACKFONT = scale_image(pygame.image.load("font1.png"), 3)
TRACK = scale_image(pygame.image.load("track.png"), 0.9)
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Follow the track!")

RWIDTH = 15
RHEIGHT = 25
VEHICLE = pygame.Rect(100, 100, RWIDTH, RHEIGHT)

CONEIMG = scale_image(pygame.image.load("cone.jpg"), 0.03)

FPS = 60

#Cone classes
class OrangeCones(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = CONEIMG
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class YellowCones(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = CONEIMG
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class BlueCones(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = CONEIMG
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

#General Vehicle characteristics
class GlobalVehicle:  
    def __init__(self, max_vel, rotation_vel):  
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.x, self.y = self.START_POS
        self.acceleration = 0.038
        self.width = RWIDTH
        self.height = RHEIGHT
        self.gear = 0
        self.kmvel = 0
        self.angle_rad = 0

    #Vehicle rotation
    def rotate(self, left=False, right=False):  
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    #Vehicle drawing on pygame window
    def draw(self, win):
        result = rectRotated(win, self.img, self.x, self.y, self.width, self.height, (0, 0, 255), self.angle)

        self.img = result.copy()

        self.angle_rad =  (math.pi / 180) * self.angle

    #Vehicle's forward movement
    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)  
        self.move()

        self.kmvel = int(self.vel * pow(2, self.vel) * pow(2, self.vel) * pow(2, self.vel) / 2)

        if self.kmvel >= 60:
            self.kmvel = 60

        if self.kmvel>=0:
            if self.kmvel<=20:
                self.gear = "1"
            else:
                if self.kmvel<=45:
                    self.gear = "2"
                else:
                    self.gear = "3"
    #Vehicle's movement
    def move(self):
        radians = math.radians(self.angle)   
        vertical = math.cos(radians) * self.vel   
        horizontal = math.sin(radians) * self.vel    

        self.y -= vertical  
        self.x -= horizontal

#The specific vehicle's characteristics
class MyVehicle(GlobalVehicle): 
    IMG = VEHICLE
    START_POS = (180, 260)

    #Vehicle's speed reduction
    def reduce_speed(self):  
        self.vel = max(self.vel - self.acceleration / 2, 0)   
        self.move()

        self.kmvel = int(self.vel * pow(2, self.vel) * pow(2, self.vel) * pow(2, self.vel) / 2)
        if self.kmvel >= 60:
            self.kmvel = 60
        if self.kmvel>0:
            if self.kmvel<=20:
                self.gear = "1"
            else:
                if self.kmvel<=45:
                    self.gear = "2"
                else:
                    self.gear = "3"
        else:
            if self.kmvel==0:
                self.gear = "Neutral"

    #Bounce back when collision
    def bounce_back(self):
        if np.abs(self.vel) != 0:
            if (self.vel) >0:
                self.vel = -self.vel/np.abs(self.vel)#antistrefo thn taxuthta
                self.move()           
        else:
            self.vel = -0.5

    #Respawn            
    def respawn(self):  
        self.vel = 0
        self.angle = 0
        (self.x, self.y) = (180, 260)  
        self.move()

#Game Node
class GamePublisher(Node):
    def __init__(self):
        super().__init__('Game_publisher')
        pygame.init()
        pygame.font.init()

        self.score = 200 #Gia na exei kati na xasei ston prvto gyro kai na mhn parei svarna toys kwnous strathgika
        self.lap = 0
        self.lapscore = 0
        self.laphelper = self.lap

        self.text_font = pygame.font.SysFont("Arial", 25)
        self.text_font1 = pygame.font.SysFont("Arial", 20)
        self.text_font2 = pygame.font.SysFont("Arial", 40)
        self.orangecones = pygame.sprite.Group()
        self.orangefile = open('orangecones.txt', 'r')
        self.orangeconeslist = []
        self.orangecolor = "orange"
        self.orangecone= []

        self.yellowcones = pygame.sprite.Group()
        self.yellowfile = open('yellowcones.txt', 'r')
        self.coneslist = []
        self.yellowcolor = "yellow"
        self.yellowcone= []

        self.bluecones = pygame.sprite.Group()
        self.bluefile = open('bluecones.txt', 'r')
        self.blueconeslist = []
        self.bluecone= []
        self.bluecolor = "blue"

        self.my_vehicle = MyVehicle(2, 4)

        self.clock = pygame.time.Clock()
        self.helper = True

        self.images = [(BLACKFONT, (-200,-200)), (TRACK, (0,0)), (FINISH, (FINISH_POS))]

        self.publisher_x = self.create_publisher(Int32, 'topic_x', 10)
        self.publisher_y = self.create_publisher(Int32, 'topic_y', 10)
        self.publisher_lap = self.create_publisher(Int32, 'topic_lap', 10)
        self.publisher_vel = self.create_publisher(Int32, 'topic_vel', 10)
        self.publisher_gear = self.create_publisher(String, 'topic_gear', 10)
        
        self.subscriber = self.create_subscription(Float32, 'topic_throttle', self.throttle_cb , 10)
        self.subscriber = self.create_subscription(Float32, 'topic_steering', self.steering_cb , 10)
        self.subscriber = self.create_subscription(Bool, 'topic_respawn', self.respawn_cb , 10)

        self.pose_pub = self.create_publisher(Twist, 'base_link', 10)
        self.broadcaster_vehicle = TransformBroadcaster(self)
        self.pose_sub = self.create_subscription(Twist, 'base_link', self.handle_vehicle_pose, 10)

        self.static_broadcaster_odom = StaticTransformBroadcaster(self)
        self.make_transforms_odom()
        self.pose_msg_pub = self.create_publisher(PoseStamped, 'topic_pose', 10)

        self.pcd_blue_publisher = self.create_publisher(PointCloud2, 'topic_blue_pcd', 10)
        self.pcd_yellow_publisher = self.create_publisher(PointCloud2, 'topic_yellow_pcd', 10)
        self.pcd_orange_publisher = self.create_publisher(PointCloud2, 'topic_orange_pcd', 10)

        self.points_blue = np.array([[130, 900-141-406+13+13, 0], [114, 900-122-406+13+13, 0], [107, 900-231-406+13+13, 0], [106, 900-356-406+13+13, 0], [126, 900-481-406+13+13, 0], [218, 900-571-406+13+13, 0], \
                                [311, 900-667-406+13+13, 0], [358, 900-596-406+13+13, 0], [397, 900-474-406+13+13, 0], [516, 900-434-406+13+13, 0], [623, 900-493-406+13+13, 0], [646, 900-614-406+13+13, 0], [694, 900-643-406+13+13, 0], \
                                [693, 900-519-406+13+13, 0], [657, 900-412-406+13+13, 0], [527, 900-411-406+13+13, 0], [401, 900-392-406+13+13, 0], [364, 900-273-406+13+13, 0], [466, 900-213-406+13+13, 0], [595, 900-214-406+13+13, 0], \
                                [694, 900-178-406+13+13, 0], [610, 900-124-406+13+13, 0], [480, 900-123-406+13+13, 0], [336, 900-122-406+13+13, 0], [330, 900-239-406+13+13, 0], [328, 900-371-406+13+13, 0], [244, 900-456-406+13+13, 0], [137, 900-399-406+13+13, 0]])
        self.points_yellow = np.array([[15, 900-280-406+13+13, 0], [14, 900-412-406+13+13, 0], [23, 900-495-406+13+13, 0], [106, 900-590-406+13+13, 0], [198, 900-688-406+13+13, 0], [297, 900-771-406+13+13, 0], \
                                [420, 900-750-406+13+13, 0], [454, 900-630-406+13+13, 0], [504, 900-529-406+13+13, 0], [553, 900-622-406+13+13, 0], [585, 900-747-406+13+13, 0], [706, 900-778-406+13+13, 0], [786, 900-686-406+13+13, 0], \
                                [785, 900-557-406+13+13, 0], [786, 900-423-406+13+13, 0], [714, 900-323-406+13+13, 0], [587, 900-321-406+13+13, 0], [463, 900-319-406+13+13, 0], [460, 900-303-406+13+13, 0], [569, 900-305-406+13+13, 0], \
                                [702, 900-307-406+13+13, 0], [787, 900-221-406+13+13, 0], [778, 900-91-406+13+13, 0], [667, 900-33-406+13+13, 0], [536, 900-31-406+13+13, 0], [410, 900-28-406+13+13, 0], [284, 900-47-406+13+13, 0], \
                                [236, 900-165-406+13+13, 0], [236, 900-293-406+13+13, 0], [221, 900-307-406+13+13, 0], [221, 900-181-406+13+13, 0], [192, 900-58-406+13+13, 0], [69, 900-44-406+13+13, 0], [14, 900-153-406+13+13, 0]])       
        self.points_orange = np.array([[130, 900-268-406+13+13, 0], [130, 900-247-406+13+13, 0], [223, 900-247-406+13+13, 0], [223, 900-268-406+13+13, 0]])

        self.odom_pub = self.create_publisher(Odometry, 'topic_odom', 10)
        self.path_pub = self.create_publisher(Path, 'topic_path', 10)
        self.odom_sub_path = self.create_subscription(Odometry, 'topic_odom', self.handle_odom_path, 10)
        self.path = Path()
        self.path.header.frame_id = "map"

        self.start = self.create_subscription(Bool, 'start_game', self.gameRun, 10)
        self.classCones()

    #Convert odometry to path msg for foxglove visualization
    def handle_odom_path(self, msg):
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose

        self.path.header.stamp = self.get_clock().now().to_msg()
        self.path.poses.append(pose)
        self.path_pub.publish(self.path)

    #Publishers
    def general_publishers(self):
        self.publish_odometry(float(self.my_vehicle.x), float(self.my_vehicle.y), 0.0, 0.0, 0.0, float(self.my_vehicle.angle_rad + np.pi/2))
        self.publish()
        self.vehicle_pose_publisher()
        self.pub_pose_msg()
        self.pcd_blue_publish()
        self.pcd_yellow_publish()
        self.pcd_orange_publish()

    #Pointcloud msgs for cone visualization
    def point_cloud(self, points, parent_frame):
 
        ros_dtype = PointField.FLOAT32
        dtype = np.float32
        itemsize = np.dtype(dtype).itemsize  

        data = points.astype(dtype).tobytes()
        fields = [PointField(name=n, offset=i * itemsize, datatype=ros_dtype, count=1) for i, n in enumerate('xyz')]
        header = std_msgs.msg.Header(frame_id=parent_frame)

        return PointCloud2(header=header, height=1, width=points.shape[0], is_dense=False, is_bigendian=False, fields=fields, point_step=(itemsize * 3), row_step=(itemsize * 3 * points.shape[0]), data=data)

    def pcd_blue_publish(self):
        self.pcd_blue = self.point_cloud(self.points_blue, 'map')
        self.pcd_blue_publisher.publish(self.pcd_blue)

    def pcd_yellow_publish(self):
        self.pcd_yellow = self.point_cloud(self.points_yellow, 'map')
        self.pcd_yellow_publisher.publish(self.pcd_yellow)

    def pcd_orange_publish(self):
        self.pcd_orange = self.point_cloud(self.points_orange, 'map')
        self.pcd_orange_publisher.publish(self.pcd_orange)

    #Publish vehicle's pose
    def vehicle_pose_publisher(self):
        self.pose = Twist()
        self.pose.linear.x = float(self.my_vehicle.x - 180)
        self.pose.linear.y = float(self.my_vehicle.y - 260)
        self.pose.linear.z = 0.0
        self.pose.angular.x = 0.0
        self.pose.angular.y = 0.0
        self.pose.angular.z = float(self.my_vehicle.angle_rad)

        self.pose_pub.publish(self.pose)

    #Quaternion from Euler
    def quaternion_from_euler(self, ai, aj, ak):
        ai /= 2.0
        aj /= 2.0
        ak /= 2.0
        ci = math.cos(ai)
        si = math.sin(ai)
        cj = math.cos(aj)
        sj = math.sin(aj)
        ck = math.cos(ak)
        sk = math.sin(ak)
        cc = ci*ck
        cs = ci*sk
        sc = si*ck
        ss = si*sk

        q = np.empty((4, ))
        q[0] = cj*sc - sj*cs
        q[1] = cj*ss + sj*cc
        q[2] = cj*cs - sj*sc
        q[3] = cj*cc + sj*ss

        return q
    
    #Posestamped msg
    def pub_pose_msg(self):
        self.pose_msg = PoseStamped()
        self.pose_msg.header.stamp = self.get_clock().now().to_msg()
        self.pose_msg.header.frame_id = 'odom'
        self.pose_msg.pose.position.x = float(self.my_vehicle.x - 180)
        self.pose_msg.pose.position.y = -float(self.my_vehicle.y - 260)
        self.pose_msg.pose.position.z = 0.0
        q = self.quaternion_from_euler(0.0, 0.0, float(self.my_vehicle.angle_rad + np.pi/2))
        self.pose_msg.pose.orientation.x = q[0]
        self.pose_msg.pose.orientation.y = q[1]
        self.pose_msg.pose.orientation.z = q[2]
        self.pose_msg.pose.orientation.w = q[3]

        self.pose_msg_pub.publish(self.pose_msg) 
    
    #Odometry msg
    def publish_odometry(self, x, y, z, ai, aj, ak):
        if (pygame.key.get_pressed()[pygame.K_a]) or (pygame.key.get_pressed()[pygame.K_d]):
            self.my_vehicle.rotation_vel = 4
        elif self.my_vehicle.rotation_vel == 3:
            self.my_vehicle.rotation_vel = 4
        else:
            self.my_vehicle.rotation_vel = 0

        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.child_frame_id = 'base_link'
        msg.twist.twist.linear.x = float(self.my_vehicle.vel * np.sin(self.my_vehicle.angle_rad))
        msg.twist.twist.linear.y = float(self.my_vehicle.vel * np.cos(self.my_vehicle.angle_rad))
        msg.twist.twist.linear.z = 0.0
        msg.twist.twist.angular.x = 0.0
        msg.twist.twist.angular.y = 0.0
        msg.twist.twist.angular.z = float(self.my_vehicle.rotation_vel)
        msg.pose.pose.position.x = x 
        msg.pose.pose.position.y = -y + 510
        msg.pose.pose.position.z = z
        q = self.quaternion_from_euler(ai, aj, ak)
        msg.pose.pose.orientation.x = q[0]
        msg.pose.pose.orientation.y = q[1]
        msg.pose.pose.orientation.z = q[2]
        msg.pose.pose.orientation.w = q[3]
        self.odom_pub.publish(msg)
    
    #Map-odom tf
    def make_transforms_odom(self):
        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'odom'

        t.transform.translation.x = float(180)
        t.transform.translation.y = float(260)
        t.transform.translation.z = float(0)
        quat = self.quaternion_from_euler(0.0, 0.0, 0.0)
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]

        self.static_broadcaster_odom.sendTransform(t)

    #odom-base_link tf
    def handle_vehicle_pose(self, msg): #Xrhsimopoio to Twist
        t = TransformStamped()

        self.pose_msg1 = msg

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = self.pose_msg1.linear.x
        t.transform.translation.y = -self.pose_msg1.linear.y
        t.transform.translation.z = self.pose_msg1.linear.z

        q = self.quaternion_from_euler(self.pose_msg1.angular.x, self.pose_msg1.angular.y, self.pose_msg1.angular.z)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]

        self.broadcaster_vehicle.sendTransform(t)

    #Respawn callback
    def respawn_cb(self, msg):
        self.score = 200
        self.lapscore = 0
        if self.score <= 0:
            self.score = 0
        self.my_vehicle.vel = 0
        self.my_vehicle.angle = 0
        (self.my_vehicle.x, self.my_vehicle.y) = (180, 260) 

    #Throttle callback (move_forward)
    def throttle_cb(self, acceleration):   
        self.my_vehicle.acceleration = 0.038
        self.my_vehicle.vel = min(self.my_vehicle.vel + self.my_vehicle.acceleration, self.my_vehicle.max_vel) 

        radians = math.radians(self.my_vehicle.angle)  
        vertical = math.cos(radians) * self.my_vehicle.vel  
        horizontal = math.sin(radians) * self.my_vehicle.vel   

        self.my_vehicle.y -= vertical 
        self.my_vehicle.x -= horizontal

    #Steering callback (left-right)
    def steering_cb(self, steering):
        if steering.data <=0.0 :
            self.my_vehicle.angle = self.my_vehicle.angle + 3
            self.my_vehicle.rotation_vel = 3
        elif steering.data > 0.0:
            self.my_vehicle.angle = self.my_vehicle.angle - 3
            self.my_vehicle.rotation_vel = 3

    #Draw text on pygame surface
    def draw_text(self, window, text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        window.blit(img, (x,y))

    #Cones' coordinates
    def classCones(self):
        for k in self.orangefile:
            i = self.orangefile.readline()
            j = self.orangefile.readline()
            rect = pygame.Rect(int(i), int(j), 10 ,10)
            self.orangeconeslist.append(rect)

            self.orangecone.append(OrangeCones(int(i), int(j)))
        self.orangefile.close()
        for i in self.orangecone:
            self.orangecones.add(i)

        for k in self.yellowfile:
            i = self.yellowfile.readline()
            j = self.yellowfile.readline()
            rect = pygame.Rect(int(i), int(j), 10 ,10)
            self.coneslist.append(rect)

            self.yellowcone.append(YellowCones(int(i), int(j)))
        self.yellowfile.close()
        for i in self.yellowcone:
            self.yellowcones.add(i)

        for k in self.bluefile:
            i = self.bluefile.readline()
            j = self.bluefile.readline()
            bluerect = pygame.Rect(int(i), int(j), 10 ,10)
            self.blueconeslist.append(bluerect)

            self.bluecone.append(BlueCones(int(i), int(j)))
        self.bluefile.close()
        for i in self.bluecone:
            self.bluecones.add(i)

    #Keybinds to move the vehicle
    def MoveVehicle(self, vehicle):
        keys = pygame.key.get_pressed()
        moved = False 

        if keys[pygame.K_a]:
            self.my_vehicle.rotate(left=True)
        if keys[pygame.K_d]:
            self.my_vehicle.rotate(right=True)
        if keys[pygame.K_w]:
            moved = True
            self.my_vehicle.move_forward()
        if not moved:
            self.my_vehicle.reduce_speed()
 
    #Draw on pygame surface
    def draw(self, window, images, finish):  
        for img, pos in images:
            window.blit(img, pos)

        for h in self.orangecones:
            h.image.fill(self.orangecolor)
            window.blit(h.image,h.rect)

        for i in self.yellowcones:
            i.image.fill(self.yellowcolor)
            window.blit(i.image,i.rect)

        for j in self.bluecones:
            j.image.fill(self.bluecolor)
            window.blit(j.image,j.rect)
        self.my_vehicle.draw(window)

    #Run the game 
    def gameRun(self, msg):
        self.general_publishers()

        #Draw on pygame window
        self.draw(WIN, self.images, FINISH)
            
        pygame.draw.circle(WIN, "black", (780,20), 50)
        self.draw_text(WIN, "x=" +str(int(self.my_vehicle.x)), self.text_font1, "orange", 750, 10)
        self.draw_text(WIN, "y=" +str(int(self.my_vehicle.y)), self.text_font1, "orange", 750, 30)

        pygame.draw.circle(WIN, "black", (20,730), 150)
        self.draw_text(WIN, "Gear", self.text_font, "orange", 40, 730) 
        if self.my_vehicle.gear == "Neutral":
            self.draw_text(WIN, str(self.my_vehicle.gear), self.text_font2, "orange", 15, 760)
        else:
            self.draw_text(WIN, "     " +str(self.my_vehicle.gear), self.text_font2, "orange", 15, 760)
        self.draw_text(WIN, "Speed", self.text_font, "orange", 30, 630)
        if self.my_vehicle.kmvel < 10:
            self.draw_text(WIN, str(self.my_vehicle.kmvel), self.text_font2, "orange", 55, 660)
        else:
            self.draw_text(WIN, str(self.my_vehicle.kmvel), self.text_font2, "orange", 45, 660)

        pygame.draw.circle(WIN, "black", (285,525), 65)
        self.draw_text(WIN, "Score", self.text_font, "orange", 257, 480)
        if self.score != 0:
            if self.score > 100:
                self.draw_text(WIN, str(self.score), self.text_font2, "orange", 255, 510)
            else:
                self.draw_text(WIN, str(self.score), self.text_font2, "orange", 265, 510)
        else:
            self.draw_text(WIN, str(self.score), self.text_font2, "orange", 275, 510)

        pygame.draw.circle(WIN, "black", (229,30), 40)
        self.draw_text(WIN, "Lap", self.text_font, "orange", 210, 2)
        self.draw_text(WIN, str(self.lapscore), self.text_font2, "orange", 220, 26)
        
        #Handling events (collisions etc)
        for event in pygame.event.get():   
            if event.type == pygame.QUIT:
                self.helper = False
                pygame.quit() 
                exit()
        self.MoveVehicle(self.my_vehicle)

        if (int(self.my_vehicle.y) < 270) and (int(self.my_vehicle.y) > 260) and (int(self.my_vehicle.x) > 130) and (int(self.my_vehicle.x) < 223):
            self.lap = self.lap + 1
        while (self.laphelper!=self.lap) and (int(self.my_vehicle.y) < 240) and (int(self.my_vehicle.y) > 230) and (int(self.my_vehicle.x) > 130) and (int(self.my_vehicle.x) < 223):
            self.lapscore = self.lapscore + 1
            self.laphelper = self.lap
            self.score = self.score + 200

        if pygame.Rect.collidelist(self.my_vehicle.img, self.coneslist) != -1:
            if self.my_vehicle.kmvel >= 0.5:
                self.score = self.score - 50
            self.my_vehicle.bounce_back()
        if pygame.Rect.collidelist(self.my_vehicle.img, self.blueconeslist) != -1:
            if self.my_vehicle.kmvel >= 0.5:
                self.score = self.score - 50
            self.my_vehicle.bounce_back()
        if pygame.Rect.collidelist(self.my_vehicle.img, self.orangeconeslist) != -1:
            if self.my_vehicle.kmvel >= 0.5:
                self.score = self.score - 50
            self.my_vehicle.bounce_back()

        if self.my_vehicle.x < 0:
            self.my_vehicle.respawn()
            self.score = 200
            self.lapscore = 0
        if self.my_vehicle.x > 810:
            self.my_vehicle.respawn()
            self.score = 200
            self.lapscore = 0
        if self.my_vehicle.y < 0:
            self.my_vehicle.respawn()
            self.score = 200
            self.lapscore = 0
        if self.my_vehicle.y > 810:
            self.my_vehicle.respawn()
            self.score = 200
            self.lapscore = 0
        if pygame.key.get_pressed()[pygame.K_r]:
            self.my_vehicle.respawn()
            self.score = 200
            self.lapscore = 0
        if self.score <= 0:
            self.score = 0

        pygame.display.update()

    #Publish information about the vehicle        
    def publish(self):
        msg1 = Int32()
        msg1.data = int(self.my_vehicle.x)
        self.publisher_x.publish(msg1)

        msg2 = Int32()
        msg2.data = int(self.my_vehicle.y)
        self.publisher_y.publish(msg2)

        msg3 = Int32()
        msg3.data = int(self.lapscore)
        self.publisher_lap.publish(msg3)

        msg4 = Int32()
        msg4.data = int(self.my_vehicle.kmvel)
        self.publisher_vel.publish(msg4)

        msg5 = String()
        msg5.data = str(self.my_vehicle.gear)
        self.publisher_gear.publish(msg5)
    
    
def main(args=None):
    rclpy.init(args=args)
    
    game_publisher = GamePublisher()

    rclpy.spin(game_publisher)

    pygame.quit()
    game_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
