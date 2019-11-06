itiot
=

A itergenerateous micropython microframework and an integrated toolchain
for developing IoT applications on micro-controller units (MCU).

The idea behind `itiot` framework is to use **python iterators** to create **data pipes** by **chaining generators** to **build pipes** where data flows. You can then compose basic pipes to create more sophisticated data flows, in a layered approach. It is also an abstraction layer for a unified programming API to speak with MCU and electronic components (`itiot.devices`).

`./mcu` is a CLI tool that integrates an MCU toolchain for prototyping and deployment workflow, with scripting and automation capabilities.

*We are still in a prototyping phase and you are welcome to fork and pull request !
Just keep it minimal.*

Installation
-
Alternatively, you can run the automated installation script
to integrate this component to your workflow
```
curl https://github.com/damiencorpataux/itiot/master/mcu | sh
```
You are welcome to report errors at https://github.com/damiencorpataux/itiot/issues.

Usage
-
Get information from the **CLI tool**
```
./mcu
```
```
ITIOT MCU management tool - https://github.com/damiencorpataux/itiot

Usage:
      ./mcu [<command>] [<arg>]

  Commands:
      install             - Install itself here (/Users/damien/dev/itiot)
      toolchain           - Install itiot toolchain software on this computer (3rd-party open-source, see below)

      drop [file] [dest]  - Batch commands flash, deps, build & copy, for 1-step MCU setup
      test [file] [dest]  - Batch commands copy & terminal, usually for dev purpose

      flash               - Download and flash micropython firmware to MCU, erasing
      deps                - Build and copy itiot dependencies to MCU (build in ./build/lib, copy to /pyboard)
      build [raw]         - Copy itiot library to MCU (copy to /pyboard)
                            if raw, do not minify
      copy [file] [dest]  - Copy file or directory to MCU

      terminal            - Open a terminal to MCU (press ^a then ^x to exit)
      shell [cmd]         - Open shell to MCU, optionally executing cmd (press ^d to exit)
      ls [file]           - List files on MCU flash, alias of command 'shell ls -la /pyboard' (press ^d to abort)
                            when file is specified, + will be replaced with FLASH_PATH (/pyboard)

      lint [file]         - Lint file (default: examples/tutorial.py)
                            for now, it only executes the given file with micropython (#todo: make useful linting)

  Arguments:
      [file] defaults to: examples/tutorial.py
      [dest] defaults to: main.py

  Config:
      - CONFIG=./config
      - DEVICE=/dev/tty.usbserial-0001
      - FIRMWARE_URL=http://micropython.org/resources/firmware/esp32-idf3-20190529-v1.11.bin
      - DEPS_SOURCE=./build/lib
      - BUILD_PATH=./build
      - FLASH_PATH=/pyboard
      + to override configuration parameters, type for example 'DEVICE=/dev/usb0 ./mcu'
      + or specify a config file with CONFIG env variable

  Toolchain:
      - micropython: (3, 4, 0)
      - esptool: esptool.py v2.8
      - rshell: 0.0.26
      - picocom: picocom v3.1

  USB ports:
      - /dev/cu.Bluetooth-Incoming-Port <-- Serial Device: ...
      - /dev/cu.usbserial-0001 <-- USB Serial Device 10c4:ea60 with vendor 'Silicon Labs' serial '00...
```
In this case, use `/dev/cu.usbserial`.
From now on, you can run `./mcu` by typing `DEVICE=/dev/cu.usbserial ./mcu <command>`.
For example, run the command `terminal` by typing:
```
DEVICE=/dev/ttyUSB0 ./mcu terminal
```
Replace `/dev/ttyUSB0`
with something you found in the **USB Ports** section of `./mcu`.

**Flash software to your device** -
this will run all the commands needed to setup your MCU up and running
a basic logic to check if your plateform is ready for fun !
```
DEVICE=/dev/ttyUSB0 ./mcu drop
```

**Try an example**
```
ls -1 examples
DEVICE=/dev/ttyUSB0 ./mcu test examples/tutorial.py
```

**In case** your device stops responding, you can **erase and flash** it again
(this will erase your device)
```
DEVICE=/dev/ttyUSB0 ./mcu drop
```

Examples
-
Have a look at the directoy `examples`. You can start with `examples/tutorial.py`:
```
./mcu drop examples/tutorial.py
```
Or just browse it at https://github.com/damiencorpataux/itiot/tree/master/examples.

Configuration
-
You can **override configuration parameters with shell environment variables**, eg:
```
DEVICE=/dev/my-usb ./mcu
```
and you should see the help screen showing your custom value for `DEVICE`.

Or you can **edit the config file** located at `./config`.

Or you can **create your own config somewhere** file and specify its location, eg:
```
CONFIG=~/itiot.conf ./mcu
```

Develop your application
-
**Create a workspace** in an arbitrary location.
For simplicity, we create the directory ´myproject´ directly in the root directory of itiot, in other words: in directory that contains `examples`:
```
mkdir myproject
```

**Create your application** - say, Hello World application:
```
echo "print('-*- H E L L O   W O R L D -*-')" > myproject/main.py
```

**Deploy your application on your MCU** - well just copy the files:
```
./mcu copy myproject/*
```

**Test your application** by looking at the terminal console:
```
./mcu terminal
```
Can you see `-*- H E L L O   W O R L D -*-` somewhere before the prompt `>>>` ?

You can also use the shorthand command `test`
to perform commands `copy`, then `terminal` in one step.
```
./mcu test myproject/*
```
2 cents to workflow efficiency  ^^

Version
-
Following semantic versioning, https://semver.org/.

Project names could be: itiot, pipeiot, flowiot, streamiot, ioterator...

Contribute
-
### Install a development environment
**Checkout repository** - thanks for playing !
```
git clone git@github.com:damiencorpataux/itiot.git
cd itiot

git checkout dev  # we like free speech and draft beer
```
For pull requests, just fork it.

**Install the toolchain components** -
this will install a minimalistic toolchain on you computer
```
./mcu toolchain
```

Test it by running examples
```
./mcu drop && ./mcu term
```

Avoid loosing time on stupid syntax errors (i **love** this one):
```
./mcu lint && ./mcu build && ./mcu test examples/tutorial.py
```
The command `lint` returns non-zero exit code on compilation failure.

### Create `device`s and `filter`s
The micropython environment is meant to stay minimal and uncluttered, IOW: KISS.

Therefore, the `itiot` module contains a few devices implementations -
yet they should be kept to a minimin and boil down to a very generic and ubiquitous
components or abstractions.

**You are welcome to create your own components !**
To publish your component, use `pip3` repository and name your package
using the conventional prefix
  * `micropython-itiot-device-` for `Device` components
  * `micropython-itiot-filter-` for `Filter` components
  * etc.
