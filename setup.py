from setuptools import setup, find_packages

setup(
    name="youtube-title-updater",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client>=2.0.0",
        "google-auth-oauthlib>=0.4.0",
        "google-auth-httplib2>=0.1.0",
        "urllib3>=2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "youtube-title-updater=youtube_updater.__main__:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A GUI application for automatically updating YouTube live stream titles",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="youtube livestream title updater gui",
    url="https://github.com/yourusername/youtube-title-updater",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
