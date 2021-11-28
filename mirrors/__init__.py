# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
Retrieve a type specific mirror, with the most basic being a filesystem mirror.
"""

import six

from .base import Mirror
from .s3 import MirrorS3
from .ghcr import MirrorGHCR


def from_dict(d, name=None):
    """
    Retrieve a mirror from a dictionary, typically the loaded spack mirrors.yaml
    """
    if isinstance(d, six.string_types):
        return Mirror(d, name=name)

    mirror_type = d.get('type')

    # The base type is also s3, we could nix this
    if mirror_type == "s3":
        return MirrorS3(d['fetch'], d['push'], name)
    if mirror_type == "ghcr":
        return MirrorGHCR(d['fetch'], d['push'], name)

    # Default is a filesystem / non-branded mirror
    return Mirror(d['fetch'], d['push'], name)


def get_mirror(fetch_url, push_url=None, name=None, **kwargs):
    """
    Given basic information, retrieve a specific mirror type, or default.
    """
    return Mirror(fetch_url, push_url, name)
