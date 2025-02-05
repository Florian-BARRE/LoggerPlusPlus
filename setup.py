from setuptools import setup, find_packages

setup(
    name="loggerplusplus",
    version="0.1.1",
    author="Florian BARRE",
    author_email="florian.barre78@gmail.com",
    description="LoggerPlusPlus is an enhanced Python logging module with colorized output, "
                "customizable themes, improved multi-logger management, and optimized display for better readability",
    long_description=open("./README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Florian-BARRE/LoggerPlusPlus",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        "colorama>=0.4.6",
        "contourpy>=1.3.1",
        "cycler>=0.12.1",
        "fonttools>=4.55.8",
        "kiwisolver>=1.4.8",
        "matplotlib>=3.10.0",
        "numpy>=2.2.2",
        "packaging>=24.2",
        "pillow>=11.1.0",
        "pyparsing>=3.2.1",
        "python-dateutil>=2.9.0.post0",
        "six>=1.17.0",
    ],
    include_package_data=True,
)
