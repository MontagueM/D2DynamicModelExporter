import gf
import numpy as np
import binascii


def get_float16(selection):
    selection = gf.get_flipped_hex(selection, 4)
    mantissa_bitdepth = 15
    exp_bitdepth = 15 - mantissa_bitdepth
    bias = 2 ** (exp_bitdepth - 1) - 1
    mantissa_division = 2 ** mantissa_bitdepth
    int_fs = int(selection, 16)
    mantissa = int_fs & 2 ** mantissa_bitdepth - 1
    mantissa_abs = mantissa / mantissa_division
    exponent = (int_fs >> mantissa_bitdepth) & 2 ** exp_bitdepth - 1
    negative = int_fs >> mantissa_bitdepth
    if exponent == 0:
        flt = mantissa_abs * 2 ** (bias - 1)
    else:
        flt = (1 + mantissa) * 2 ** (exponent - bias)
    return flt * (-1) ** negative


def get_signed_int(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits-1)):
        value -= 1 << bits
    return value


def func(test_hex, intended, v_flip):
    test = get_signed_int(gf.get_flipped_hex(test_hex, 4), 16)
    if v_flip:
        test *= -1
    unsign = int(gf.get_flipped_hex(test_hex, 4), 16)
    negative = unsign >> 15
    q = (1 + test/(2**15 - 1)) * 2 ** (-1)
    print(round(q, 6), negative, get_float16(test_hex))
    print(test_hex, intended)

func('FF7F', 0.999985, False)
func('E958', 0.847305, False)
func('8478', 0.970764, False)
print('\n')
func('0180', 0.99985, True)
func('4C84', 0.983215, True)
func('6C89', 0.963196, True)
# func('0180', -0.99985, True)
# func('4C84', -0.983215, True)
# func('6C89', -0.963196, True)
print('\n')
func('E000', 0.503418, False)
func('C9FF', 0.499161, False)
func('9C80', 0.002380, False)