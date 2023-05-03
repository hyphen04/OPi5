# -*- coding: utf-8 -*-
# Copyright (c) 2018 Richard Hull
# See LICENSE.md for details.

#EDITED BY hyphen04
#GITHUB - https://github.com/hyphen04

import functools
from copy import deepcopy
from OPi.constants import BOARD, BCM, SUNXI, CUSTOM


class _sunXi(object):

    def __getitem__(self, value):

        offset = ord(value[1]) - 65
        pin = int(value[2:])

        assert value[0] == "P"
        assert 0 <= offset <= 25
        assert 0 <= pin <= 31

        return (offset * 32) + pin


_pin_map = {
    # Physical pin to actual GPIO pin
    BOARD: {
	3:47,
	5:46,
	7:54,
	8:131,
	10:132,
	12:29,
	11:138,
	13:139,
	15:28,
	16:59,
	18:58,
	19:49,
	21:48,
	22:92,
	24:52,
	23:50,
	26:35
    },

    # User defined, initialized as empty
    CUSTOM: {}
}


def set_custom_pin_mappings(mappings):
    _pin_map[CUSTOM] = deepcopy(mappings)


def get_gpio_pin(mode, channel):
    assert mode in [BOARD]
    return _pin_map[mode][channel]


bcm = functools.partial(get_gpio_pin, BCM)
board = functools.partial(get_gpio_pin, BOARD)
sunxi = functools.partial(get_gpio_pin, SUNXI)
custom = functools.partial(get_gpio_pin, CUSTOM)
