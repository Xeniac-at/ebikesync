from distutils.core import setup

setup(
    name='ebikesync',
    version='0.2.0',
    packages=["ebikesync", "ebikesync.input", "ebikesync.output"],
    package_dir={'ebikesync': 'src/ebikesync'},
    url='https://github.com/Xeniac-at/ebikesync',
    license='GPLv3+',
    author='Christian Berg',
    author_email='xeniac.github@xendynastie.at',
    description='A seleniumbot to sync your ebike stats with other services.',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: Console',
        'Topic :: Text Processing :: Markup :: HTML'
        'Intended Audience :: End Users/Desktop',
    ],
    python_requires=">=3.7, <4",
    install_requires=["selenium~=4.5", "xdg~=5.0", "xvfbwrapper"],
    scripts=['bin/ebikesync'],
)
