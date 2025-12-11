from PIL import Image, ImageDraw

# Create icon images
sizes = [16, 48, 128]

for size in sizes:
    # Create a new image with green background
    img = Image.new('RGB', (size, size), color='#34c759')
    
    # Save the image
    img.save(f'images/icon-{size}.png')
    print(f'Created icon-{size}.png')

print('Done! All icons created.')