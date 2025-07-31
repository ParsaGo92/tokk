#!/usr/bin/env python3
"""
Setup script for OJS Exploit Framework.

This package provides a comprehensive exploit framework for Open Journal Systems (OJS)
with advanced vulnerability assessment, exploitation, and post-exploitation capabilities.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ojs-exploit-framework",
    version="1.0.0",
    author="OJS Exploit Framework Team",
    author_email="security@example.com",
    description="Advanced exploit framework for Open Journal Systems (OJS)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ojs-exploit-framework/ojs-exploit-framework",
    project_urls={
        "Bug Tracker": "https://github.com/ojs-exploit-framework/ojs-exploit-framework/issues",
        "Documentation": "https://github.com/ojs-exploit-framework/ojs-exploit-framework/wiki",
        "Source Code": "https://github.com/ojs-exploit-framework/ojs-exploit-framework",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Security Researchers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.12.0",
            "black>=21.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.15.0",
        ],
        "full": [
            "selenium>=4.0.0",
            "playwright>=1.20.0",
            "mitmproxy>=8.0.0",
            "burp-rest-api>=0.1.0",
            "frida>=15.0.0",
            "frida-tools>=9.0.0",
            "pwntools>=4.0.0",
            "scapy>=2.4.0",
            "python-nmap>=0.7.0",
            "paramiko>=2.8.0",
            "netaddr>=0.8.0",
            "dnspython>=2.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ojs-exploit=main:cli",
            "ojs-recon=main:recon",
            "ojs-scan=main:scan",
            "ojs-exploit=main:exploit",
            "ojs-post=main:post",
            "ojs-chain=main:chain",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "config/*.json",
            "docs/*.md",
            "tests/*.py",
            "*.md",
            "*.txt",
            "*.yml",
            "*.yaml",
        ],
    },
    keywords=[
        "security",
        "penetration-testing",
        "exploit",
        "vulnerability-assessment",
        "web-security",
        "ojs",
        "open-journal-systems",
        "php",
        "sql-injection",
        "xss",
        "file-upload",
        "deserialization",
        "waf-bypass",
        "evasion",
        "red-team",
        "offensive-security",
    ],
    platforms=["any"],
    license="MIT",
    zip_safe=False,
    # Additional metadata
    maintainer="OJS Exploit Framework Team",
    maintainer_email="security@example.com",
    download_url="https://github.com/ojs-exploit-framework/ojs-exploit-framework/archive/v1.0.0.tar.gz",
    provides=["ojs_exploit_framework"],
    requires_python=">=3.8",
    # Security considerations
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Security Researchers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
        "Framework :: Pytest",
        "Typing :: Typed",
    ],
    # Package discovery
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    # Data files
    data_files=[
        ("config", ["config/payloads.json", "config/evasion_rules.json"]),
        ("docs", ["docs/vuln_analysis.md", "docs/mitigation.md", "docs/api.md"]),
        ("tests", ["tests/test_exploits.py"]),
    ],
    # Scripts
    scripts=[
        "main.py",
    ],
    # Dependencies
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "colorama>=0.4.4",
        "rich>=10.0.0",
        "click>=8.0.0",
        "cryptography>=3.4.0",
        "pycryptodome>=3.10.0",
        "phpserialize>=1.3",
        "python-magic>=0.4.24",
        "pillow>=8.0.0",
        "paramiko>=2.8.0",
        "netaddr>=0.8.0",
        "dnspython>=2.2.0",
        "python-nmap>=0.7.0",
        "scapy>=2.4.0",
        "pwn>=4.0.0",
        "pwntools>=4.0.0",
        "frida>=15.0.0",
        "frida-tools>=9.0.0",
        "pytest>=6.0.0",
        "pytest-asyncio>=0.18.0",
        "aiohttp>=3.8.0",
        "asyncio-throttle>=1.0.0",
        "websockets>=10.0.0",
        "selenium>=4.0.0",
        "playwright>=1.20.0",
        "mitmproxy>=8.0.0",
        "burp-rest-api>=0.1.0",
    ],
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
            "tox>=3.24.0",
            "coverage>=6.0.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.15.0",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
        "full": [
            "selenium>=4.0.0",
            "playwright>=1.20.0",
            "mitmproxy>=8.0.0",
            "burp-rest-api>=0.1.0",
            "frida>=15.0.0",
            "frida-tools>=9.0.0",
            "pwntools>=4.0.0",
            "scapy>=2.4.0",
            "python-nmap>=0.7.0",
            "paramiko>=2.8.0",
            "netaddr>=0.8.0",
            "dnspython>=2.2.0",
        ],
    },
    # Entry points for command line tools
    entry_points={
        "console_scripts": [
            "ojs-exploit=main:cli",
            "ojs-recon=main:recon",
            "ojs-scan=main:scan",
            "ojs-exploit=main:exploit",
            "ojs-post=main:post",
            "ojs-chain=main:chain",
        ],
    },
    # Include package data
    include_package_data=True,
    package_data={
        "": [
            "config/*.json",
            "docs/*.md",
            "tests/*.py",
            "*.md",
            "*.txt",
            "*.yml",
            "*.yaml",
        ],
    },
    # Keywords for PyPI
    keywords=[
        "security",
        "penetration-testing",
        "exploit",
        "vulnerability-assessment",
        "web-security",
        "ojs",
        "open-journal-systems",
        "php",
        "sql-injection",
        "xss",
        "file-upload",
        "deserialization",
        "waf-bypass",
        "evasion",
        "red-team",
        "offensive-security",
        "cybersecurity",
        "ethical-hacking",
        "security-testing",
        "web-application-security",
    ],
    # Platform support
    platforms=["any"],
    # License
    license="MIT",
    # Don't create a zip file
    zip_safe=False,
    # Additional metadata
    maintainer="OJS Exploit Framework Team",
    maintainer_email="security@example.com",
    download_url="https://github.com/ojs-exploit-framework/ojs-exploit-framework/archive/v1.0.0.tar.gz",
    provides=["ojs_exploit_framework"],
    requires_python=">=3.8",
)