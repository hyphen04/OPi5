
# GPIO setup in Orange Pi 5

Pinout setup for orange pi 5 




## Download

Clone OPi repository

```bash
  mkdir Your-project-name
  cd Your-project-name
  git clone https://github.com/hyphen04/OPi5.git
  #if Folder name is OPi-main rename it into OPi
```


## Led Blinking Test

Create Python file 

```bash
  touch BlinkLed.py 
```


## BlinkLed.py

Paste this code into BlinkLed.py

```bash
  import OPi5.GPIO as GPIO
  pin = 13   					# physical pin number of gpio
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(pin, GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)

```
You can find out physical pin number using this command:
```bash 
  gpio readall
```

