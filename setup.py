from setuptools import setup, find_packages


# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name="rallyrobopilot",  # Replace with your package name
    version="0.1",
    author="Louis Lettry, Cédric Travelletti",
    author_email="",
    description="",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="",  # Replace with your repo URL if available
    packages=find_packages(),  # Automatically find and include packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Adjust license as needed
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=requirements,
)
