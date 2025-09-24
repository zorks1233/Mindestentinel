from setuptools import setup, find_packages 
 
setup( 
    name="mindestentinel", 
    version="0.1.0", 
    packages=find_packages(where="src"), 
    package_dir={"": "src"}, 
    include_package_data=True, 
    install_requires=[ 
        "uvicorn>=0.23.2", 
        "fastapi>=0.95.0", 
        "psutil>=5.9.0", 
        "pyyaml>=6.0", 
        "sqlite3>=2.6.0", 
    ], 
    entry_points={ 
        "console_scripts": [ 
            "mindest=mindestentinel:main", 
        ], 
    }, 
    author="Mindestentinel Team", 
    description="Autonomes KI-System mit Selbstlernfähigkeit", 
    long_description=open("README.md").read(), 
    long_description_content_type="text/markdown", 
    url="https://github.com/yourusername/mindestentinel", 
    classifiers=[ 
        "Programming Language :: Python :: 3", 
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent", 
    ], 
    python_requires=">=3.8", 
) 
