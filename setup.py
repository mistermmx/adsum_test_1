from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    required_packages = f.read().splitlines()

setup(
    name="adsum_test_1",
    version="0.1.0",
    description="An Apache Airflow-based project with AWS backend",
    author="Victor Grobler",
    author_email="grobler.victor@gmail.com",
    url="https://github.com/mistermmx/adsum_test_1",
    packages=find_packages(),
    install_requires=required_packages,
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
        ],
    },
    include_package_data=True,
)
