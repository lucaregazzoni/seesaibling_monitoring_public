# Underwater Monitoring Unit Software Documentation
> [!CAUTION]
> The software for the monitoring unit is being tested, use at your own risk!

This github repository serves as an construction and implementation documentation for an autonomous, battery-powered, underwater monitoring unit developed within the [arctic char project of the ZHAW Wädenswil](https://www.zhaw.ch/de/forschung/projekt/76339). 
The system is a prototype, that is in continuous development; over the last months various functionalities were added.

## Specifications of the monitoring unit
The monitoring unit (MONI) is an autonomous underwater monitoring unit (prototype) that is used for a low-cost, continuous, video and audio monitoring of underwater habitats.

### Specifications
* Depth rating: 
	* hydrophone rated for 80 m
	* with aluminum casing up to 500 m
* Video or long-time exposures (1080p)
* Lighting (dimmable, max. 1’500 lumens)
* Audio recording (max. sampling rate 192kHz/24bit)
	* frequency range ≈ 10 Hz up to 96 kHz 
* Data logging 
	* Temperature
	* Voltage, Current (and Power)
	* Leak sensors
	* Event logging
* Power consumption (unoptimized)
	* Base consumption ≈ 1.5 W
	* Max consumption ≈ 15 W 
* Battery life
	* Continuous monitoring ≈ 10 days (with continuous full power lighting)
	* Interval monitoring > 30 to 60 days

### Technical components
The main component for system control is a Raspberry Pi 4 that is driving various components, such as a camera, light, sensors (leak, temperature), indicator lights. Electrical consumption is measured by a seperate Raspberry Pi Pico WM communicating via UART with the main control unit. Following a simplified technical schematic of the system components and its wiring.
![MONI_Systemübersicht](https://github.com/user-attachments/assets/6f1015de-a5ac-48a3-a45f-f1e54854840a)


### v2.0, 2025.03.07
The rpi can be reached within the ZHAW network (not at the moment 07.03.2025, only by mobile hotspot); with similar credentials to this:
```
	hostname: ...
	username: ...
	password: ...
	port: 22
```
afterwards do:
```bash
	# invoke a screen session:
	screen -S monitoring
	# invoke venv session 
	source seesaibling/env/bin/activate
	cd seesaibling/scripts
	python3 cst_vid_thread.py
```
You'll be prompted to define the type of operation: `Choose between predefined [p], test [t] or custom [c] operation:`: 
- For `p` a predefined duration is used as length variables for the main interval, recording of video and audio and data logging.
- `t` is for testing outputs and calibration (interval, `30 s`, data logging `5 s`, video `1 to 20 s`, audio `7 to 23 s`, light `10 to 20 s`).
- `c` allows for custom adjustment of input parameters (see console output).
  
Detach from the screen session using **CTRL + A** and **D** and quit the `ssh` session.
To shutdown the rpi type `sudo shutdow now` to shutdown immediately (else add a number instead of now for minutes) and turn off the rotary button on the back side of the monitoring unit.

<details>

<summary> Previous version (earlier 29.10.2024) </summary>

### v1.3, 2025.01.28

The rpi can be reached within the ZHAW network; with similar credentials to this:
```
	hostname: ...
	username: ...
	password: ...
	port: 22
```
afterwards do:
```bash
	# invoke a screen session:
	screen -S monitoring
	# invoke venv session 
	source env/bin/activate
	cd seesaibling/scripts
	sudo /home/pi/env/bin/python3 cst_vid.py
```
You'll be prompted to define `duration`, `increment`, and `log_duration` via user input, whereafter the rpi starts taking videos for the defined duration within an increment.
Detach from the screen session using **CTRL + A** and **D** and quit the `ssh` session.
To shutdown the rpi type `sudo shutdow now` to shutdown immediately (else add a number instead of now for minutes) and turn off the rotary button on the back side of the monitoring unit.

### v1.2, 2024.12.27

The rpi can be reached within the ZHAW network; with similar credentials to this:
```
	hostname: ...
	username: ...
	password: ...
	port: 22
```
afterwards do:
```bash
	# invoke a screen session:
	screen -S monitoring
	# invoke venv session 
	source env/bin/activate
	cd seesaibling/scripts
	sudo /home/pi/env/bin/python3 cst_photo.py
```
You'll be prompted to define `duration`, `increment`, `log_duration` and light color via user input, whereafter the rpi starts taking five pictures for the defined duration and increment.
Detach from the screen session using **CTRL + A** and **D** and quit the `ssh` session.
To shutdown the rpi type `sudo shutdow now` to shutdown immediately (else add a number instead of now for minutes).

### v1.1, 2024.10.29

The rpi can be reached within the ZHAW network (but not at the moment); with similar credentials to this:
```
	hostname: ...
	username: ...
	password: ...
	port: 22
```
afterwards do:
```bash
	# invoke a screen session:
	screen -S monitoring
	# invoke venv session 
	source env/bin/activate
	cd seesaibling/scripts
	sudo /home/pi/env/bin/python3 cst_photo.py
```
You'll be prompted to define `duration`, `increment` and `log_duration` via user input, whereafter the rpi starts filming for the defined duration and increment.
Detach from the screen session using **CTRL + A** and **D** and quit the `ssh` session.

### v1, 2024.10.11

At the moment, the rpi can be reached within the ZHAW network using Putty and any SFTP client and the following credentials:

```bash
	hostname: ...
	username: ...
	password: ...
	port: 22
```

afterwards do:

```bash
	cd seesaibling
	ls #just to display all files, find cst_vid.py
	python3 cst_vid.py
```

You'll be prompted to define `duration` and `increment` via user input, whereafter the rpi starts filming for the defined duration and increment.

</details>


## Things to do
- [x] How to "start" the rpi in the field?
	- [x] How to start script via `ssh`, while script keeps running after session is terminated? (use screen session)
- [x] Setting up LEDs and programming them to turn on/off (use `cst.py` script to test)
- [x] Setting up voltage and current measurement of battery (using ina260 described below)
	- [x] First test using the load of LEDs
- [x] draw and order new pcbs for the rgb LEDs (done and working, 21.11.2024)
- [x] test running duration of monitoring unit (assuming constant power usage)
- [x] wet test of monitoring unit and checking lighting underwater
- [x] finalise wiring for the monitoring unit (revised on 28.01.2025)
- [x] add sensors:
	- [x] temperature (difficulty: 3/10, 28.01.2025)
	- [x] leak sensor (difficulty: 3/10, 28.01.2025)
	- [x] hydrophone  (difficulty: 8/10)
  	


## Setting up the rpi
### Connecting the rpi-zero with the internet
Since a normal, out of the box, connection to the network is not possible in most university networks (or wasn't atleast for me) it's necessary to contact the ICT to register your device (e.g. an rpi) in the iot network. For this the MAC-adress of the device needs to be known and supplied to the ICT. There are multiple ways to get the MAC-adress; easiest is probably typing `ifconfig` in a shell and reading it out under `wlan0: ... ether`. The ICT will afterwards register a hostname for the rpi, which has to be changed under `raspi-config`:
```bash
	sudo raspi-config
```
Navigate to and change according to the ICT information:
```
	1 System options
		> S4 Hostname
```
For the present version (03.10.2024) of the rpi the following information is valid for the iot-ZHAW network:
```
	hostname: [Redacted]
	password: [Redacted]
```
The network access can be adapted using `sudo raspi-config` and navigating to:
```
	1 System options
		> S1 Wireless LAN
```

### Installation of a pip packages, e.g. neopixel for usage of led strips
Since recently, it is required that a virtual environment is setup before installation of non debian maintained packages via pip. For this the python virtual environment `venv` has to be installed, which is included in `python3-full`. Create a `venv` as following:
```bash
python3 -m venv env --system-site-package
```
whereby:
- `venv` evokes a virtual Environment
- `env` Name of the Environment
- `--system-site-package` should allow for usage of packages installed in `venv` without it being activated

To reenter or reactivate the `venv` (e.g. after a reboot) it has to be activated every time as follows:
```
source env/bin/activate
```
You can see if you are currently in a `venv` by looking at the console output:
```bash
	pi@[redacted]:~ $
	# changes to:
	(env) pi@[redacted]:~ $
```
Whereby the `(env)` refers to the name you have given your virtual environment in the first place.
Being in the virtual environment, here packages should be installable via pip3. For the control of the LED stripes, we are requiring the libraries `rpi_ws281x` and `adafruit-circuitpython-neopixel`:
```bash
	pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```
Contrary to what is stated (even in the adafruit guide) `sudo` does **not** work in the `venv` and will lead to an error! I read that sudo should not be used anyways because it enables system wide installation, which the virtual environment tries to inhibit because otherwise the system base installation can be corrupted.

To run scripts that envoke packages that were installed within a virtual environment, they have to be called with the absolute path, so that installed modules can be found within `venv`:
```bash
	sudo /home/pi/env/bin/python3 test.py
	# contrary to simply running:
	sudo python3 test.py ...
```
In this case `sudo` is used because the blinka or board packages requires sudo permissions, usually it is not necessary. At this point (03.10.2024) it is unclear, whether the scripts should be called within the venv or not?

#### Helpful links:
- [Installing pip on a rpi](https://fleetstack.io/blog/install-pip-raspberry-pi-guide)
- [Virtual environment setup guide](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
- [Virtual environment usage on an rpi](https://learn.adafruit.com/python-virtual-environment-usage-on-raspberry-pi/more-venv-details)
- [Setting up and using the NeoPixels library and ws281x leds](https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage)
- [Rpi GPIO Pin out](https://pinout.xyz/#)
- [rgb color tables](https://www.rapidtables.com/web/color/RGB_Color.html)
- [The used rgb leds for the project](https://www.reichelt.com/ch/de/shop/produkt/entwicklerboards_-_led_pixel_ws2812b-376753)

### Using the Picamera2 library for camera control
We want to control the camera of the rpi using python, since we are using advanced control algorithms to check for lighting requirements etc. For basic usage and testing if the camera works libcamera is usually preinstalled on the rpi or is easily installed and can be tested, e.g. using `libcamera-hello` in a shell. For python usage, check if libcamera for python is currently installed or install it as following:
```bash
	sudo apt install -y python3-picamera2 --no-install-recommends
```
Whereby `--no-install-recommends` leaves out all GUI dependencies, which in this case are unnecessary.
#### Helpful links:
- [Libcamera2 on Github](https://github.com/raspberrypi/picamera2)
- [Libcamera2 documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

## Setting up voltage and current measurement of the battery pack
We are using a Adafruit INA260 sensor to measure the voltage and current that is used, respectively we are mainly interested in the voltage drop over time from the battery. This will facilitate:
- forecasting the maximal measurement duration of the monitoring unit
- having a save emergency shutdown when voltage decreases beyond a defined level

To set the `rpi` up, firstly adafruits ina260 library has to be installed (do this in the `venv` as described above):
```bash
pip3 install adafruit-circuitpython-ina2
```
Most probably other dependencies such as a general circuitpython installation amongst others are required for this to function properly.

#### Helpful links:
- [ina260 documentation](https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout/python-circuitpython)

## Various setup tips and problems
### Running a script independently of a ssh session
When you run a script in an ssh session it will be terminated if you exit it. Thus, you will need a command line window manager such as `screen` with which you can activate sessions and keep them run independently of ssh sessions.
You can install screen by typing:
```bash
sudo apt-get install screen
```
Once this is done using `screen` is simple. You can type the following for starting a new screen session:
```bash
screen -S monitoring
```
Whereby `monitoring` refers to the active session. With pressing **CTRL + A** followed by **D** you can detach from a session and leave the ssh session. The script will be continuously executed.
To resume a screen session after logging in into `ssh`, type the following (if there is only a single `screen` session
```bash
screen -r # to resume a single session
screen ls #list all current running screen sessions
screem -r monitoring # resume a specific session
```
Terminating a screen can be done when resuming a session and pressing **CTRL + A** followed by **K** and **y**,or simply typing ``screen -XS monitoring quit``

#### Helpful links
- [Screen documentation tips](https://wiki.ubuntuusers.de/Screen/)

### Upload of file via sftp failed
Could either be a problem of the directory not being writeable or the file itself being owned by root and, thus, it's not possible to overwrite a file. To change the directories permissions:
```bash
sudo chmod 777 /name/of/file/or/directory
```
or alternative for more restricted access:
```bash
sudo chmod 755 /name/of/file/or/directory
```
#### Helpful links
- [Understanding Linux file permissions](https://www.multacom.com/faq/password_protection/file_permissions.htm)
- [Changing file permissions](https://askubuntu.com/questions/1340627/how-do-i-edit-a-write-protected-file)

### setting up ffmpeg for playing/editing .h264 video 
VLC-player doesn't properly display .h264 video exports. You can check it out yourself by watching a .h264 video and looking at lost frames information (under `Tools > Media Information > Statistics`).

Really the only possible lightweight alternative is to download and install `ffmpeg`. Since `ffmpeg` only supplies raw code a prebuilt version has to be download as `.z7` from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
It's easiest to follow a guide (e.g. [from here](https://phoenixnap.com/kb/ffmpeg-windows)) for the manual installation and adding the necessary variable to `:PATH`. After the installation typing `ffplay \filename.format` in a command line interface can be used to play practically any video format. 
Typically, ZHAW `<cmd>` is in your `U:` drive, thus, files can just be dropped there to be watched. Compared to most video players, `ffmpeg` has **no** GUI, thus, everything has to be done via `cmd` (which makes you a lot cooler than simply opening VLC).
`ffmpeg` open up a lot of different possibilities, such as playing videos at a certain frame rate (and many more), triming and editing video fully automatically in a `cmd` environment (which will be usefull when we'll analyze video later on in the project).
To play videos a certain frame rate, for instance, use the following command:
```
ffplay -f h264 file.264 -vf "setpts=2.0*N/FRAME_RATE/TB"
```
#### Helpful links:
- [What you can do with ffmpeg](https://shotstack.io/learn/how-to-use-ffmpeg/)

### setting up an I2S microphone (SPH0645)
Actually surprisingly simple following this guide from [adafruit](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test). 
However adding ```dtoverlay=googlevoicehat-soundcard``` followed by ```dtparam=audio=off``` (to disable all other audio inputs)  in ```/boot/firmware/config.txt``` did not load the ```dtoverlay``` correctly. 
Force loading it using ```sudo dtoverlay googlevoicehat-soundcard``` did the trick (shout out to ChatGPT!). You can display whether the ```googlevoicehat-soundcard``` is loaded correctly using ```cat /proc/asound/cards``` , where it should display as an audio device
```bash
0 [vc4hdmi        ]: vc4-hdmi - vc4-hdmi
                      vc4-hdmi
 1 [sndrpigooglevoi]: RPi-simple - snd_rpi_googlevoicehat_soundcar
                      snd_rpi_googlevoicehat_soundcard
```
In the example above device ```0``` refers to the built-in hdmi device (the hdmi plug of the rpi), device 1 refers to the ```googlevoicehat-soundcard```.
A list of capture hardware devices can be generated using:
```bash
arecord -l
```
Where it should show up as following:
```bash
**** List of CAPTURE Hardware Devices ****
card 1: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0: Google voiceHAT SoundCard HiFi voicehat-hifi-0 [Google voiceHAT SoundCard HiFi voicehat-hifi-0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```
Testing the microphone can be done using: 
```bash
arecord -D plughw:1 -c1 -r 48000 -f S32_LE -t wav -V mono -v file.wav
```
and/or by adding a defined duration for recording:
```bash
arecord -D plughw:1 -c1 -r 48000 -d 10 -f S32_LE -t wav -V mono -v file.wav
```

#### Helpful links: 
- [adafruit i2s sph0645 documentation](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test)
- [arecord documentation](https://linux.die.net/man/1/arecord)
- [rpi config.txt documentation](https://www.raspberrypi.com/documentation/computers/configuration.html)
