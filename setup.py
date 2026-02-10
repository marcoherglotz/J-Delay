from setuptools import setup

setup(
    name="j-delay",
    version="1.0.0",
    description="JACK Audio Input Latency Compensator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Marco Herglotz",
    url="https://github.com/YOUR_USERNAME/J-Delay",  # Update this before publishing!
    license="GPLv3",
    py_modules=["J-Delay"],
    install_requires=[
        "JACK-Client",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "j-delay=J-Delay:main",  # Requires refactoring J-Delay.py to have a main() function exposed properly if imported
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
