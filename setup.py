from setuptools import setup, find_packages

setup(
    name="youtube_title_updater",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-api-python-client>=2.0.0",
        "google-auth-oauthlib>=0.4.6",
        "google-auth-httplib2>=0.1.0",
        "PyQt6>=6.4.0",
        "urllib3>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "py2app>=0.28.0",  # For macOS app bundling
            "pyinstaller>=5.0.0",  # For Windows app bundling
        ],
    },
    entry_points={
        "console_scripts": [
            "youtube-title-updater=youtube_updater.gui:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A desktop application for automatically updating YouTube live stream titles",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="youtube livestream title updater gui",
    url="https://github.com/yourusername/youtube-title-updater",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
)
