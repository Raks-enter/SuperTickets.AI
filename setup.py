"""
SuperTickets.AI Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="supertickets-ai",
    version="1.0.0",
    author="SuperTickets.AI Team",
    author_email="support@supertickets.ai",
    description="AI-powered support triage system with Kiro agents and FastAPI MCP microservice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/SuperTickets.AI",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/SuperTickets.AI/issues",
        "Documentation": "https://docs.supertickets.ai",
        "Source Code": "https://github.com/your-org/SuperTickets.AI",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Email",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.6.0",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
            "mkdocs-swagger-ui-tag>=0.6.6",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "sentry-sdk[fastapi]>=1.38.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "supertickets-ai=mcp_service.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_service": [
            "*.json",
            "*.yaml",
            "*.yml",
        ],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "support",
        "triage",
        "fastapi",
        "kiro",
        "mcp",
        "bedrock",
        "supabase",
        "gmail",
        "calendar",
        "tickets",
        "automation",
    ],
)