from setuptools import setup, find_packages

setup(
    name="clarea-engine",
    version="0.1.0",
    description="Open-source Decision Intelligence & Marketing Analytics Engine for Claude",
    author="Robert Villa",
    author_email="robjesusvilla@gmail.com",
    packages=find_packages(include=["clarea", "clarea.*"]),
    install_requires=[
        "pydantic>=2.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0"
    ],
    entry_points={
        "console_scripts": [
            "clarea=clarea.cli:app",
        ],
    },
    python_requires=">=3.10",
)
