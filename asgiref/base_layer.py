from __future__ import unicode_literals

import fnmatch
import re
import six


class BaseChannelLayer(object):
    """
    Base channel layer object; outlines the core API and contains some handy
    reuseable code bits. You don't have to inherit from this, but it might
    save you time.
    """

    def __init__(self, expiry=60, group_expiry=86400, capacity=100, channel_capacity=None):
        self.expiry = expiry
        self.capacity = capacity
        self.group_expiry = group_expiry
        self.channel_capacity = self.compile_capacities(channel_capacity or {})

    ### ASGI API ###

    extensions = []

    class ChannelFull(Exception):
        pass

    class MessageTooLarge(Exception):
        pass

    def send(self, channel, message):
        raise NotImplementedError()

    def receive_many(self, channels, block=False):
        raise NotImplementedError()

    def new_channel(self, pattern):
        raise NotImplementedError()

    ### ASGI Group API ###

    def group_add(self, group, channel):
        raise NotImplementedError()

    def group_discard(self, group, channel):
        raise NotImplementedError()

    def send_group(self, group, message):
        raise NotImplementedError()

    ### ASGI Flush API ###

    def flush(self):
        raise NotImplementedError()

    ### Capacity utility functions

    def compile_capacities(self, channel_capacity):
        """
        Takes an input channel_capacity dict and returns the compiled list
        of regexes that get_capacity will look for as self.channel_capacity/
        """
        result = []
        for pattern, value in channel_capacity.items():
            # If they passed in a precompiled regex, leave it, else intepret
            # it as a glob.
            if hasattr(pattern, "match"):
                result.append((pattern, value))
            else:
                result.append((re.compile(fnmatch.translate(pattern)), value))
        return result

    def get_capacity(self, channel):
        """
        Gets the correct capacity for the given channel; either the default,
        or a matching result from channel_capacity. Returns the first matching
        result; if you want to control the order of matches, use an ordered dict
        as input.
        """
        for pattern, capacity in self.channel_capacity:
            if pattern.match(channel):
                return capacity
        return self.capacity

    def match_type_and_length(self, name):
        if (len(name) < 100) and (not isinstance(name, six.text_type)):
            return True
        return False

    ### Name validation functions

    channel_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+((\?|\!)[\d\w\-_.]+)?$")
    group_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+$")

    def valid_channel_name(self, name):
        if self.match_type_and_length(name):
            if bool(self.channel_name_regex.match(name)):
                return True
        raise TypeError("Channel name must be a valid unicode string containing only alphanumerics, hyphens, or periods.")

    def valid_group_name(self, name):
        if self.match_type_and_length(name):
            if bool(self.group_name_regex.match(name)):
                return True
        raise TypeError("Group name must be a valid unicode string containing only alphanumerics, hyphens, or periods.")
