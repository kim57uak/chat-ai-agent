#!/usr/bin/env python3
"""
Chat AI Agent Setup Script
Cross-platform packaging for Mac and Windows
"""

from setuptools import setup, find_packages
import os
import sys

# Read requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="chat-ai-agent",
    version="1.0.0",
    description="다양한 MCP 서버와 연동하여 도구를 사용할 수 있는 AI 채팅 에이전트",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chat AI Agent Contributors",
    author_email="",
    url="https://github.com/your-repo/chat-ai-agent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'chat-ai-agent=main:main',
        ],
    },
    package_data={
        '': ['*.json', '*.md', '*.txt', '*.spec'],
        'ui': ['*.py'],
        'core': ['*.py'],
        'mcp': ['*.py'],
        'tools': ['*.py'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)