from setuptools import setup, find_packages
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="AWS Factory Simulator",  # Replace with your application name
    version="0.1.0",
    description="An application for managing machines and production processes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Cem Akpolat",  # Replace with your name or team name
    author_email="cem.akpolat@sva.de",  # Replace with your email address
    url="https://github.com",  # Replace with your GitHub repo URL if available
    packages=find_packages(),  # Automatically find all packages
    include_package_data=True,
    install_requires=requirements,  # Use dependencies from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Replace with the minimum Python version your app supports
    entry_points={
        "console_scripts": [
            "run-app=app:main",  # This assumes you have a `main` function in `app.py` to start your application
        ],
    },
)
