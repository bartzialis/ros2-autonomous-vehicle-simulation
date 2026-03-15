# Bartzialis

import pygame
import math

#Scales the image by 2x if I give factor = 2 etc
def scale_image(img, factor):
    size = round(img.get_width() * factor), round(img.get_height() * factor)

    return pygame.transform.scale(img, size)

#Rotate vehicle function (is usable but not used in my project)
def rotate_center(win, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(
        center=image.get_rect(topleft=top_left).center)     
    win.blit(rotated_image, new_rect.topleft)

#Rotate and draw the vehicle
def rectRotated(win, rect, x, y, width, height, color, rotation):
    points = []
    # The distance from the center of the rectangle to
    # one of the corners is the same for each corner.
    radius = math.sqrt((height / 2)**2 + (width / 2)**2)
    # Get the angle to one of the corners with respect
    # to the x-axis.
    angle = math.atan2(height / 2, width / 2)
    # Transform that angle to reach each corner of the rectangle.
    angles = [angle, -angle + math.pi, angle + math.pi, -angle]
    # Convert rotation from degrees to radians.
    rot_radians = (math.pi / 180) * rotation
    # Calculate the coordinates of each point.
    for angle in angles:
        y_offset = -1 * radius * math.sin(angle + rot_radians)
        x_offset = radius * math.cos(angle + rot_radians)
        points.append((x + x_offset, y + y_offset))

    polygonrect = pygame.draw.polygon(win, color, points)

    y_offset = -1 * math.sin(angle + rot_radians)
    x_offset = math.cos(angle + rot_radians)
    pygame.Rect.update(rect, x + x_offset - 12.515, y + y_offset - 12.5, 25 , 25)

    polygonrect = pygame.Rect.clamp(polygonrect, rect)

    return polygonrect
