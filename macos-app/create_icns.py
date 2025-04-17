from PIL import Image
import os
import subprocess

def create_icns():
    try:
        # Open the PNG image
        img = Image.open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico'))
        
        # Create a temporary directory for icon files
        temp_dir = os.path.join(os.path.dirname(__file__), 'icon.iconset')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create different sizes for the icon
        sizes = [
            ('icon_16x16.png', 16),
            ('icon_16x16@2x.png', 32),
            ('icon_32x32.png', 32),
            ('icon_32x32@2x.png', 64),
            ('icon_128x128.png', 128),
            ('icon_128x128@2x.png', 256),
            ('icon_256x256.png', 256),
            ('icon_256x256@2x.png', 512),
            ('icon_512x512.png', 512),
            ('icon_512x512@2x.png', 1024)
        ]
        
        # Generate all icon sizes
        for filename, size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(os.path.join(temp_dir, filename))
        
        # Convert iconset to icns
        icns_path = os.path.join(os.path.dirname(__file__), 'icon.icns')
        subprocess.run(['iconutil', '-c', 'icns', temp_dir, '-o', icns_path])
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir)
        
        print("ICNS file created successfully!")
        
    except Exception as e:
        print(f"Error creating ICNS file: {str(e)}")

if __name__ == "__main__":
    create_icns() 