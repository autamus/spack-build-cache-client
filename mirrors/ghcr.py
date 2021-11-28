# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
An S3 specific mirror.
"""

import spack.spec
import spack.util.spack_json as sjson
import llnl.util.tty as tty
import spack.util.url as url_util
import spack.util.web as web_util

from six.moves.urllib.error import URLError

import codecs

from .base import Mirror, MirrorDownload


class MirrorGHCR(Mirror):

    @property
    def fetch_url(self):
        return self._fetch_url["url"]

    @property
    def push_url(self):
        if self._push_url is None:
            return self._fetch_url["url"]
        return self._push_url["url"]

    def get_download_tarball(self, match):
        parts = [x.strip('/') for x in match['spec_url'].split('/_cache/')[1:]]
        oras = self._fetch_url['oras'] + "/" + "/".join(parts)
        return oras.replace('spec.json', 'spack')

    def get_prefixes(self):
        """
        The traditional spack cache seems to assume that the user must know
        the previous prefix, which is usually some date and build_cache. This
        isn't good for discoverability, so instead here we use an endpoint
        to get the prefixes, and then iterate through them (newest date first)
        until we find a match (or do not). This means if the build cache has
        a matching entry for any date we will find it.
        """
        prefix_url = "%s/manifest/dates/" % self._fetch_url['url']
        return self._get_request(prefix_url)

    def get_manifest(self):
        """
        Get the build cache manifest, with packages and keys
        """
        keys_url = "%s/manifest/" % self._fetch_url['url']
        return self._get_request(keys_url)

    def get_fingerprint_links(self):
        """
        Return a lookup of links (to .pub) and key metadata with each
        """
        tty.debug('Finding public keys in {0}'.format(
            url_util.format(self.fetch_url)))

        manifest = self.get_manifest()
        if not manifest:
            return []
        return manifest.get('keys', [])

    def fetch_spec(self, specfile_name, _=None):
        """
        Fetch an object from GitHub packages, supporting both json and yaml
        """
        prefixes = self.get_prefixes()

        # Empty result means not found in the cache
        result = None
        json_url = None
        raw_url = prefixes['url_prefix']

        # Look for the specfile name directory (we only use json)
        for prefix in prefixes.get('dates', []):
            json_url = "%s%s/%s" % (raw_url, prefix, specfile_name)
            try:
                _, _, json_file = web_util.read_from_url(json_url)
                result = sjson.load(codecs.getreader('utf-8')(json_file))
                break
            except (URLError, web_util.SpackWebError):
                pass

        if result:
            spec = spack.spec.Spec.from_dict(result)
            return MirrorDownload(spec, json_url, self).to_dict()
