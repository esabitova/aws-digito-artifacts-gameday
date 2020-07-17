from setuptools import find_packages, setup

setup(
    name="AwsDigitoSsmDocumentSamples",
    version="1.0",
    # declare your packages
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    test_suite='test',
)
