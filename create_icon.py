from PIL import Image, ImageDraw
import os

# Create a new image with a transparent background
icon_size = 256
img = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a dark gray background circle
circle_margin = 10
circle_size = icon_size - (2 * circle_margin)
draw.ellipse(
    [circle_margin, circle_margin, circle_margin + circle_size, circle_margin + circle_size],
    fill=(45, 45, 45, 255)
)

# Draw an outer "radar" ring
ring_width = 8
ring_margin = 20
ring_size = icon_size - (2 * ring_margin)
draw.ellipse(
    [ring_margin, ring_margin, ring_margin + ring_size, ring_margin + ring_size],
    outline=(0, 255, 0, 255),
    width=ring_width
)

# Draw radar lines
center = icon_size // 2
for angle in [45, 135, 225, 315]:  # Diagonal lines
    # Calculate end points
    length = (icon_size - (2 * ring_margin)) // 2
    end_x = center + int(length * 0.7071 * (1 if angle < 180 else -1))  # cos(45°) ≈ 0.7071
    end_y = center + int(length * 0.7071 * (1 if angle < 270 and angle > 90 else -1))
    draw.line([(center, center), (end_x, end_y)], fill=(0, 255, 0, 128), width=2)

# Save as ICO with multiple sizes
img.save('icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])