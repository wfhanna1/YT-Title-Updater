from PIL import Image
import os

def convert_to_ico():
    try:
        # Open the PNG image
        img = Image.open(os.path.join(os.path.dirname(__file__), 'logo.png'))
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create different sizes for the icon
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icons = []
        
        for size in sizes:
            # Resize the image
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icons.append(resized)
        
        # Save as ICO file
        icons[0].save(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico'), 
                     format='ICO', 
                     sizes=[(i.width, i.height) for i in icons])
        print("Icon created successfully!")
        
    except Exception as e:
        print(f"Error creating icon: {str(e)}")

if __name__ == "__main__":
    convert_to_ico() 