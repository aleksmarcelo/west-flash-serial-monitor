from setuptools import setup

from custom_install_commands import CustomInstallCommand


setup(
    name="west-flash-serial-monitor",
    version="0.1.0",
    description="Serial monitor with pause functionality for west flash",
    author="Author",
    author_email="marcelo.aleks_AT_gmail.com",
    url="https://github.com/username/west-flash-serial-monitor",
    license="MIT",
    py_modules=["monitor", "flash", "custom_install_commands"],
    install_requires=[
        # "west",
    ],
    python_requires=">=3.6",
    cmdclass={
        'install': CustomInstallCommand,
    },
)


