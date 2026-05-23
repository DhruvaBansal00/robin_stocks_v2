from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="robin_stocks",
    version="3.5.0",
    description="A Python wrapper around the Robinhood API (with an optional MCP server)",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/jmfernandes/robin_stocks",
    author="Josh Fernandes",
    author_email="joshfernandes@mac.com",
    keywords=["robinhood", "robin stocks", "finance app", "stocks", "options", "trading", "investing", "mcp"],
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(include=["robin_stocks", "robin_stocks.*", "robin_stocks_mcp", "robin_stocks_mcp.*"]),
    install_requires=[
        "requests>=2.32.4",
        "pyotp>=2.3.0",
        "python-dotenv>=0.15.0",
        "cryptography>=46.0.5",
    ],
    extras_require={
        "mcp": ["mcp[cli]>=1.2.0"],
        "dev": ["pytest", "pytest-asyncio", "pytest-timeout", "pytest-dotenv", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [
            "robin-stocks-mcp=robin_stocks_mcp.server:main",
        ],
    },
    zip_safe=False,
)
