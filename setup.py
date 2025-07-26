from setuptools import find_packages, setup
from typing import List
def get_requirements(file_path:str)->List[str]:
    requirements = []
    with open(file_path) as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.replace("\n","") for req in requirements]
        if "-e ." in requirements:
            requirements.remove("-e .")
    return requirements

setup(
    name = 'TimeGuard',
    packages = find_packages(),
    version = '0.1.0',
    description = 'A machine learning-powered application for student time management and task monitoring',
    author = 'Pandurangareddy Kotte',
    author_email = 'kottepandurangareddy@gmail.com',
    maintainer="Tippu Salma",
    maintainer_email="tippusalmasalma@gmail.com",
    install_requires = get_requirements('requirements.txt'),
    
)