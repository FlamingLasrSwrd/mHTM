# exceptions.py
#
# Author         : James Mnatzaganian
# Contact        : http://techtorials.me
# Organization   : NanoComputing Research Lab - Rochester Institute of
# Technology
# http://www.rit.edu/kgcoe/facility/nanocomputing-research-laboratory
# http://nano.ce.rit.edu
# Date Created   : 09/27/14
#
# Description    : Module for dealing with all errors
# Python Version : 3.6.X
#
# License        : MIT License http://opensource.org/licenses/mit-license.php
# Copyright      : (c) 2015 James Mnatzaganian

"""
Exception handler for this project. This module is used for every single
exception.

G{packagetree nano_htm}
"""

__docformat__ = 'epytext'

# Native imports
import textwrap


def wrap_error(msg):
    """Wrap an error message such that it will get displayed properly.

    @param msg: The error to display.

    @return: A string containing the formatted message.
    """
    return '\n  ' + '\n  '.join(textwrap.wrap(msg, 77))


class BaseException(Exception):
    """Base class for exception handling in this program."""

    def __str__(self):
        """Allow the exception to throw the message even if it wasn't caught.

        @return: The error message.
        """
        return self.msg


class InvalidSequence(BaseException):
    """Exception raised if an item is not a supported sequence."""

    def __init__(self, seq, method):
        """Initialize this class.

        @param seq: The failed sequence object.

        @param method: The method that was missing.
        """
        self.msg = wrap_error(
            f'The object, {seq}, is not a supported sequence. \
            The object must have a "{method}" method.')


class UnsupportedFunction(BaseException):
    """Raise exception if an unsupported function is called.

    I.e. a user tried to do something he / she shouldn't be doing with that
    specific object.
    """

    def __init__(self, class_name, function_name):
        """Initialize this class.

        @param class_name: The class name of the caller.

        @param function_name: The function name of the caller.
        """
        self.msg = wrap_error(f'The object, {class_name}, \
            does not support the function {function_name}. \
            Please check your usage and try again.')


class BitMissMatch(BaseException):
    """Raise exception if the expected number of bits does not equal the supplied number of bits."""

    def __init__(self, expected, actual):
        """Initialize this class.

        @param expected: The number of expected bits.

        @param actual: The actual number of bits.
        """

        self.msg = wrap_error(f'The encoder expected {expected} bit(s), \
            but {actual} bit(s) were supplied. Please ensure that you are \
            passing the correct number of bits.')
