from setuptools import setup, find_packages

setup(
    name='cr-posideon',
    version='v0.4.1alpha',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['pika==0.11.0', 'requests==2.18.4', 'schedule==0.4.3'],
    test_require=['pytest==3.2.1', 'pytest-cov==2.5.1', 'pylint==1.7.2', 'httmock==1.2.6', 'mock==2.0.0'],
    license='MIT',
    maintainer='David Grossman',
    maintainer_email='dgrossman@iqt.org',
    description=('Machine learning toolkit to label network devices and activity.'),
    keywords='machine_learning security networking',
    url='https://github.com/CyberReboot/poseidon',
    entry_points={
        'console_scripts': [
            'poseidon-monitor = poseidon.poseidonMonitor.poseidonMonitor:main',
        ],
    },
)