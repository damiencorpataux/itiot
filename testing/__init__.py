"""
Minimal testing framework.

There are 2 ideas for a kisstupid testing workflow:

- Mock of micropython built-in modules to run code on plain python - this is stupid for it won't work

- Create a cli 'test' command that:
  1. create a test suite with:
     - script with instructions to execute on MCU that will output results
     - script that parses outputed results and map them to assertions
  1. deploy the test suite to MCU (instructions script)
  2. connect terminal to MCU
  3. parse the serial output and perform assertions (assertions script)
"""
