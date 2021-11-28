# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
An S3 specific mirror.
"""

import spack.util.spack_json as sjson
import llnl.util.tty as tty
import spack.util.url as url_util
import spack.util.web as web_util

from six.moves.urllib.error import URLError

import os
import codecs

from .base import Mirror


class MirrorS3(Mirror):

    def get_profile(self, url_type):
        if url_type == "push":
            return self._push_url['profile']
        return self._fetch_url['profile']

    def set_profile(self, url_type, profile):
        if url_type == "push":
            self._push_url["profile"] = profile
        else:
            self._fetch_url["profile"] = profile

    def get_access_pair(self, url_type):
        if url_type == "push":
            return self._push_url['access_pair']
        return self._fetch_url['access_pair']

    def set_access_pair(self, url_type, connection_tuple):
        if url_type == "push":
            self._push_url["access_pair"] = connection_tuple
        else:
            self._fetch_url["access_pair"] = connection_tuple

    def get_endpoint_url(self, url_type):
        if url_type == "push":
            return self._push_url['endpoint_url']
        return self._fetch_url['endpoint_url']

    def set_endpoint_url(self, url_type, url):
        if url_type == "push":
            self._push_url["endpoint_url"] = url
        else:
            self._fetch_url["endpoint_url"] = url

    def get_access_token(self, url_type):
        if url_type == "push":
            return self._push_url['access_token']
        return self._fetch_url['access_token']

    def set_access_token(self, url_type, connection_token):
        if url_type == "push":
            self._push_url["access_token"] = connection_token
        else:
            self._fetch_url["access_token"] = connection_token

    @property
    def fetch_url(self):
        return self._fetch_url["url"]

    @property
    def push_url(self):
        if self._push_url is None:
            return self._fetch_url["url"]
        return self._push_url["url"]

    def get_fingerprint_links(self):
        """
        Return a lookup of links (to .pub) and key metadata with each
        """
        # A mirror can define its own keys urls/index, or fall back to AWS
        keys_url = url_util.join(self.fetch_url,
                                 self._build_cache_relative_path,
                                 self._build_cache_keys_relative_path)
        keys_index = url_util.join(keys_url, 'index.json')

        tty.debug('Finding public keys in {0}'.format(
            url_util.format(self.fetch_url)))

        try:
            _, _, json_file = web_util.read_from_url(keys_index)
            json_index = sjson.load(codecs.getreader('utf-8')(json_file))
        except (URLError, web_util.SpackWebError) as url_err:
            if web_util.url_exists(keys_index):
                err_msg = [
                    'Unable to find public keys in {0},',
                    ' caught exception attempting to read from {1}.',
                ]

                tty.error(''.join(err_msg).format(
                    url_util.format(self.fetch_url),
                    url_util.format(keys_index)))

                tty.debug(url_err)

            return

        for fingerprint, _ in json_index['keys'].items():
            link = os.path.join(keys_url, fingerprint + '.pub')
            yield link
