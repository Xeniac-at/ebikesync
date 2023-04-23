# ebikesync
at this moment ebikesync uses selenium to fetch your bikestats from ebike-connect.com, and submit them to radelt.at
currently it fetches the total distance and total amplitude.

## Background
radelt.at is a platform to motivate you using your bike instead of your car.
One way to track you distance there, is to submit the current total distance from your bikecomputer and the additonal amplitude.

In a perfect world I would fetch the data with an API Call from my Boardcomputer (or a Bosch API-Server) and submit them with an REST Call to radelt.at
Meanwhile I have to use selenium instead, since Bosch's ebike-connect.com makes strong use of JavaScript.

## Requirements
* python 3
* python modules selenium and xdg
* a Browser supperted by Selenium: Firefox, Chrome, Chromium, Edge, Safari
* the Seleniumdriver for your chosen Browser, it must be in your $PATH
* XVFB and python xvfbwrapper module if you like to run the script form Linux Commandline.  
  there is a selenium remotedriver, but I haven't tested it.


## Installation
* Install the right selenium webdriver for your Browser.
* *Linux:* Copy config.ini to $HOME/.config/ebikesync/
* *Windows* Copy config.ini to %HOMEPAT%\.config\ebikesync\
* edit config.ini
* run ebikesync.py
