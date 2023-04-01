import warnings

from OPi.constants import IN, OUT
from OPi.constants import LOW, HIGH                     # noqa: F401
from OPi.constants import NONE, RISING, FALLING, BOTH   # noqa: F401
from OPi.constants import BCM, BOARD, SUNXI, CUSTOM
from OPi.constants import PUD_UP, PUD_DOWN, PUD_OFF     # noqa: F401
from OPi.pin_mappings import get_gpio_pin, set_custom_pin_mappings
from OPi import event, sysfs

_gpio_warnings = True
_mode = None
_exports = {}


def _check_configured(channel, direction=None):
    configured = _exports.get(channel)
    if configured is None:
        raise RuntimeError("Channel {0} is not configured".format(channel))

    if direction is not None and direction != configured:
        descr = "input" if configured == IN else "output"
        raise RuntimeError("Channel {0} is configured for {1}".format(channel, descr))


def getmode():
    """
    To detect which pin numbering system has been set.

    :returns: :py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM`, :py:attr:`GPIO.SUNXI`
        or :py:attr:`None` if not set.
    """
    return _mode


def setmode(mode):
    """
    You must call this method prior to using all other calls.

    :param mode: the mode, one of :py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM`,
        :py:attr:`GPIO.SUNXI`, or a `dict` or `object` representing a custom
        pin mapping.
    """
    if hasattr(mode, '__getitem__'):
        set_custom_pin_mappings(mode)
        mode = CUSTOM

    assert mode in [BCM, BOARD, SUNXI, CUSTOM]
    global _mode
    _mode = mode


def setwarnings(enabled):
    global _gpio_warnings
    _gpio_warnings = enabled


def setup(channel, direction, initial=None, pull_up_down=None):
    """
    You need to set up every channel you are using as an input or an output.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param direction: whether to treat the GPIO pin as input or output (use only
        :py:attr:`GPIO.IN` or :py:attr:`GPIO.OUT`).
    :param initial: (optional) When supplied and setting up an output pin,
        resets the pin to the value given (can be :py:attr:`0` / :py:attr:`GPIO.LOW` /
        :py:attr:`False` or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`).
    :param pull_up_down: (optional) When supplied and setting up an input pin,
        configures the pin to 3.3V (pull-up) or 0V (pull-down) depending on the
        value given (can be :py:attr:`GPIO.PUD_OFF` / :py:attr:`GPIO.PUD_UP` /
        :py:attr:`GPIO.PUD_DOWN`)

    To configure a channel as an input:

    .. code:: python

       GPIO.setup(channel, GPIO.IN)

    To set up a channel as an output:

    .. code:: python

       GPIO.setup(channel, GPIO.OUT)

    You can also specify an initial value for your output channel:

    .. code:: python

       GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)

    **Setup more than one channel:**
    You can set up more than one channel per call. For example:

    .. code:: python

       chan_list = [11,12]    # add as many channels as you want!
                              # you can tuples instead i.e.:
                              #   chan_list = (11,12)
       GPIO.setup(chan_list, GPIO.OUT)
    """
    if _mode is None:
        raise RuntimeError("Mode has not been set")

    if pull_up_down is not None:
        if _gpio_warnings:
            warnings.warn("Pull up/down setting are not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    if isinstance(channel, list):
        for ch in channel:
            setup(ch, direction, initial)
    else:
        if channel in _exports:
            raise RuntimeError("Channel {0} is already configured".format(channel))
        pin = get_gpio_pin(_mode, channel)
        try:
            sysfs.export(pin)
        except (OSError, IOError) as e:
            if e.errno == 16:   # Device or resource busy
                if _gpio_warnings:
                    warnings.warn("Channel {0} is already in use, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.".format(channel), stacklevel=2)
                sysfs.unexport(pin)
                sysfs.export(pin)
            else:
                raise e

        sysfs.direction(pin, direction)
        _exports[channel] = direction
        if direction == OUT and initial is not None:
            sysfs.output(pin, initial)


def input(channel):
    """
    Read the value of a GPIO pin.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :returns: This will return either :py:attr:`0` / :py:attr:`GPIO.LOW` /
        :py:attr:`False` or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`).
    """
    _check_configured(channel)  # Can read from a pin configured for output
    pin = get_gpio_pin(_mode, channel)
    return sysfs.input(pin)


def output(channel, state):
    """
    Set the output state of a GPIO pin.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param state: can be :py:attr:`0` / :py:attr:`GPIO.LOW` / :py:attr:`False`
        or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`.

    **Output to several channels:**
    You can output to many channels in the same call. For example:

    .. code:: python

       chan_list = [11,12]                             # also works with tuples
       GPIO.output(chan_list, GPIO.LOW)                # sets all to GPIO.LOW
       GPIO.output(chan_list, (GPIO.HIGH, GPIO.LOW))   # sets first HIGH and second LOW
    """
    if isinstance(channel, list):
        for ch in channel:
            output(ch, state)
    else:
        _check_configured(channel, direction=OUT)
        pin = get_gpio_pin(_mode, channel)
        return sysfs.output(pin, state)


def wait_for_edge(channel, trigger, timeout=-1):
    """
    This function is designed to block execution of your program until an edge
    is detected.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param trigger: The event to detect, one of: :py:attr:`GPIO.RISING`,
        :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.
    :param timeout: (optional) TODO

    In other words, the polling example above that waits for a button press
    could be rewritten as:

    .. code:: python

       GPIO.wait_for_edge(channel, GPIO.RISING)

    Note that you can detect edges of type :py:attr:`GPIO.RISING`,
    :py:attr`GPIO.FALLING` or :py:attr:`GPIO.BOTH`. The advantage of doing it
    this way is that it uses a negligible amount of CPU, so there is plenty left
    for other tasks.

    If you only want to wait for a certain length of time, you can use the
    timeout parameter:

    .. code:: python

       # wait for up to 5 seconds for a rising edge (timeout is in milliseconds)
       channel = GPIO.wait_for_edge(channel, GPIO_RISING, timeout=5000)
       if channel is None:
           print('Timeout occurred')
       else:
           print('Edge detected on channel', channel)
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    if event.blocking_wait_for_edge(pin, trigger, timeout) is not None:
        return channel


def add_event_detect(channel, trigger, callback=None, bouncetime=None):
    """
    This function is designed to be used in a loop with other things, but unlike
    polling it is not going to miss the change in state of an input while the
    CPU is busy working on other things. This could be useful when using
    something like Pygame or PyQt where there is a main loop listening and
    responding to GUI events in a timely basis.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param trigger: The event to detect, one of: :py:attr:`GPIO.RISING`,
        :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.
    :param callback: (optional) TODO
    :param bouncetime: (optional) TODO

    .. code: python

       GPIO.add_event_detect(channel, GPIO.RISING)  # add rising edge detection on a channel
       do_something()
       if GPIO.event_detected(channel):
           print('Button pressed')
    """
    _check_configured(channel, direction=IN)

    if bouncetime is not None:
        if _gpio_warnings:
            warnings.warn("bouncetime is not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    pin = get_gpio_pin(_mode, channel)
    event.add_edge_detect(pin, trigger, __wrap(callback, channel))


def remove_event_detect(channel):
    """
    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    event.remove_edge_detect(pin)


def add_event_callback(channel, callback, bouncetime=None):
    """
    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param callback: TODO
    :param bouncetime: (optional) TODO
    """
    _check_configured(channel, direction=IN)

    if bouncetime is not None:
        if _gpio_warnings:
            warnings.warn("bouncetime is not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    pin = get_gpio_pin(_mode, channel)
    event.add_edge_callback(pin, __wrap(callback, channel))


def event_detected(channel):
    """
    This function is designed to be used in a loop with other things, but unlike
    polling it is not going to miss the change in state of an input while the
    CPU is busy working on other things. This could be useful when using
    something like Pygame or PyQt where there is a main loop listening and
    responding to GUI events in a timely basis.

    .. code:: python

       GPIO.add_event_detect(channel, GPIO.RISING)  # add rising edge detection on a channel
       do_something()
       if GPIO.event_detected(channel):
           print('Button pressed')

    Note that you can detect events for :py:attr:`GPIO.RISING`,
    :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :returns: :py:attr:`True` if an edge event was detected, else :py:attr:`False`.
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    return event.edge_detected(pin)


def __wrap(callback, channel):
    if callback is not None:
        return lambda _: callback(channel)


def cleanup(channel=None):
    """
    At the end any program, it is good practice to clean up any resources you
    might have used. This is no different with OPi.GPIO. By returning all
    channels you have used back to inputs with no pull up/down, you can avoid
    accidental damage to your Orange Pi by shorting out the pins. Note that
    this will only clean up GPIO channels that your script has used. Note that
    GPIO.cleanup() also clears the pin numbering system in use.

    To clean up at the end of your script:

    .. code:: python

       GPIO.cleanup()

    It is possible that don't want to clean up every channel leaving some set
    up when your program exits. You can clean up individual channels, a list or
    a tuple of channels:

    .. code:: python

       GPIO.cleanup(channel)
       GPIO.cleanup( (channel1, channel2) )
       GPIO.cleanup( [channel1, channel2] )
    """
    if channel is None:
        cleanup(list(_exports.keys()))
        setwarnings(True)
        global _mode
        _mode = None
    elif isinstance(channel, list):
        for ch in channel:
            cleanup(ch)
    else:
        _check_configured(channel)
        pin = get_gpio_pin(_mode, channel)
        event.cleanup(pin)
        sysfs.unexport(pin)
        del _exports[channel]


class PWM:

    # To Do:
    # 1. Start tracking pwm cases to  list like _exports say _exports_pwm
    # 2. find way to check _exports against _exports_pwm to make sure there is no overlap.
    # 3. Create map of pwm pins to various boards.

    def __init__(self, chip, pin, frequency, duty_cycle_percent, invert_polarity=False):  # (pwm pin, frequency in KHz)

        """
        Setup the PWM object to control.

        :param chip: the pwm chip number you wish to use.
        :param pin: the pwm pin number you wish to use.
        :param frequency: the frequency of the pwm signal in hertz.
        :param duty_cycle_percent: the duty cycle percentage.
        :param invert_polarity: invert the duty cycle.
            (:py:attr:`True` or :py:attr:`False`).
        """

        self.chip = chip
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle_percent = duty_cycle_percent
        self.invert_polarity = invert_polarity

        try:
            sysfs.PWM_Export(chip, pin)  # creates the pwm sysfs object
            if invert_polarity is True:
                sysfs.PWM_Polarity(chip, pin, invert=True)  # invert pwm i.e the duty cycle tells you how long the cycle is off
            else:
                sysfs.PWM_Polarity(chip, pin, invert=False)  # don't invert the pwm signal. This is the normal way its used.
            sysfs.PWM_Enable(chip, pin)
            return sysfs.PWM_Frequency(chip, pin, frequency)

        except (OSError, IOError) as e:
            if e.errno == 16:   # Device or resource busy
                warnings.warn("Pin {0} is already in use, continuing anyway.".format(pin), stacklevel=2)
                sysfs.PWM_Unexport(chip, pin)
                sysfs.PWM_Export(chip, pin)
            else:
                raise e

    def start_pwm(self):  # turn on pwm by setting the duty cycle to what the user specified
        """
        Start PWM Signal.
        """
        return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, self.duty_cycle_percent)  # duty cycle controls the on-off

    def stop_pwm(self):  # turn on pwm by setting the duty cycle to 0
        """
        Stop PWM Signal.
        """
        return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, 0)  # duty cycle at 0 is the equivilant of off

    def change_frequency(self, new_frequency):
        # Order of opperations:
        # 1. convert to period
        # 2. check if period is increasing or decreasing
        # 3. If increasing update pwm period and then update the duty cycle period
        # 4. If decreasing update the duty cycle period and then the pwm period
        # Why:
        # The sysfs rule for PWM is that PWM Period >= duty cycle period (in nanosecs)

        """
        Change the frequency of the signal.

        :param new_frequency: the new PWM frequency.
        """

        pwm_period = (1 / new_frequency) * 1e9
        pwm_period = int(round(pwm_period, 0))
        duty_cycle = (self.duty_cycle_percent / 100) * pwm_period
        duty_cycle = int(round(duty_cycle, 0))

        old_pwm_period = int(round((1 / self.frequency) * 1e9, 0))

        if (pwm_period > old_pwm_period):  # if increasing
            sysfs.PWM_Period(self.chip, self.pin, pwm_period)  # update the pwm period
            sysfs.PWM_Duty_Cycle(self.chip, self.pin, duty_cycle)  # update duty cycle

        else:
            sysfs.PWM_Duty_Cycle(self.chip, self.pin, duty_cycle)  # update duty cycle
            sysfs.PWM_Period(self.chip, self.pin, pwm_period)  # update pwm freq

        self.frequency = new_frequency  # update the frequency

    def duty_cycle(self, duty_cycle_percent):  # in percentage (0-100)
        """
        Change the duty cycle of the signal.

        :param duty_cycle_percent: the new PWM duty cycle as a percentage.
        """

        if (0 <= duty_cycle_percent <= 100):
            self.duty_cycle_percent = duty_cycle_percent
            return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, self.duty_cycle_percent)
        else:
            raise Exception("Duty cycle must br between 0 and 100. Current value: {0} is out of bounds".format(duty_cycle_percent))

    def pwm_polarity(self):  # invert the polarity of the pwm
        """
        Invert the signal.
        """
        sysfs.PWM_Disable(self.chip, self.pin)
        sysfs.PWM_Polarity(self.chip, self.pin, invert=not(self.invert_polarity))
        sysfs.PWM_Enable(self.chip, self.pin)

    def pwm_close(self):
        """
        remove the object from the system.
        """
        sysfs.PWM_Unexport(self.chip, self.pin)
