import requests
from PIL import Image
from io import BytesIO

def create_icon():
    # URL of the image
    url = "https://www.stmarycoc.org/wp-content/uploads/2022/01/cropped-logo-5X5.8-1-e1727183662892.png"
    
    try:
        # Download the image
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        
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
        icons[0].save('../icon.ico', format='ICO', sizes=[(i.width, i.height) for i in icons])
        print("Icon created successfully!")
        
    except Exception as e:
        print(f"Error creating icon: {str(e)}")

if __name__ == "__main__":
    create_icon() 