# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
This is a base mirror type, e.g., for a filesystem.
"""
import ruamel.yaml.error as yaml_error
import six

import llnl.util.tty as tty

import spack.spec
import spack.util.url as url_util
import spack.util.web as web_util
import spack.util.spack_json as sjson
import spack.util.spack_yaml as syaml
from spack.util.spack_yaml import syaml_dict
from six.moves.urllib.error import URLError

import codecs


def _is_string(url):
    return isinstance(url, six.string_types)


def _display_mirror_entry(size, name, url, type_=None):
    if type_:
        type_ = "".join((" (", type_, ")"))
    else:
        type_ = ""
    print("%-*s%s%s" % (size + 4, name, url, type_))


class MirrorDownload(object):
    """
    A mirror download keeps a record of a mirror and spec to download
    """
    def __init__(self, spec, spec_url, mirror):
        self.spec = spec
        self.spec_url = spec_url
        self.mirror = mirror

    def to_dict(self):
        return {"spec": self.spec, "mirror_url": self.mirror.fetch_url,
                "mirror": self.mirror, "spec_url": self.spec_url}

    @property
    def mirror_url(self):
        return self.mirror.fetch_url


class Mirror(object):
    """A named location for storing source tarballs and binary packages

    The default used to be s3, and now they are split into two classes to
    allow for extendability or customization if needed.
    """
    def __init__(self, fetch_url, push_url=None, name=None, **kwargs):
        self._fetch_url = fetch_url
        self._push_url = push_url
        self._name = name

        # S3 puts keys alongside the key cache storage, provide if needed
        from spack.binary_distribution import _build_cache_relative_path
        from spack.binary_distribution import _build_cache_keys_relative_path
        self._build_cache_relative_path = _build_cache_relative_path
        self._build_cache_keys_relative_path = _build_cache_keys_relative_path

    def to_json(self, stream=None):
        return sjson.dump(self.to_dict(), stream)

    def to_yaml(self, stream=None):
        return syaml.dump(self.to_dict(), stream)

    def get_download_tarball(self, tarball, _=None):
        relpath = self._build_cache_relative_path
        return url_util.join(self.fetch_url, relpath, tarball)

    @staticmethod
    def from_yaml(stream, name=None):
        try:
            data = syaml.load(stream)
            return Mirror.from_dict(data, name)
        except yaml_error.MarkedYAMLError as e:
            raise syaml.SpackYAMLError("error parsing YAML spec:", str(e))

    def from_json(self, stream, name=None):
        d = sjson.load(stream)
        return self.__class__.from_dict(d, name)

    def to_dict(self):
        if self._push_url is None:
            return self._fetch_url
        else:
            return syaml_dict([
                ('fetch', self._fetch_url),
                ('push', self._push_url)])

    @staticmethod
    def from_dict(d, name=None):
        if isinstance(d, six.string_types):
            return Mirror(d, name=name)
        else:
            return Mirror(d['fetch'], d['push'], name=name)

    def display(self, max_len=0):
        if self._push_url is None:
            _display_mirror_entry(max_len, self._name, self.fetch_url)
        else:
            _display_mirror_entry(
                max_len, self._name, self.fetch_url, "fetch")
            _display_mirror_entry(
                max_len, self._name, self.push_url, "push")

    def __str__(self):
        name = self._name or ''
        if name:
            name = ' "%s"' % name

        if self._push_url is None:
            return "[Mirror%s (%s)]" % (name, self._fetch_url)

        return "[Mirror%s (fetch: %s, push: %s)]" % (
            name, self._fetch_url, self._push_url)

    def __repr__(self):
        return ''.join((
            'Mirror(',
            ', '.join(
                '%s=%s' % (k, repr(v))
                for k, v in (
                    ('fetch_url', self._fetch_url),
                    ('push_url', self._push_url),
                    ('name', self._name))
                if k == 'fetch_url' or v),
            ')'
        ))

    def _get_request(self, url, allow_fail=False):
        """
        Perform a basic get request for a URL, allow fail (or not)
        """
        try:
            _, _, json_file = web_util.read_from_url(url)
            return sjson.load(codecs.getreader('utf-8')(json_file))
        except (URLError, web_util.SpackWebError) as url_err:
            if allow_fail:
                tty.debug('Did not find {0}'.format(url))
                return
            if web_util.url_exists(url):
                err_msg = [
                    'Unable to perform request to {0},',
                    ' caught exception attempting to read from {1}.',
                ]
                tty.error(''.join(err_msg).format(url_util.format(url)))
                tty.debug(url_err)

    def fetch_spec(self, specfile_name, deprecated_specfile_name):
        """
        Fetch from S3, supporting both json and yaml, return MirrorDownload
        """
        relpath = self._build_cache_relative_path

        # First try json, and then fall back to yaml
        spec_url = url_util.join(self.fetch_url, relpath, specfile_name)

        fs = self._get_request(spec_url, allow_fail=True)
        if not fs:
            spec_url = url_util.join(self.fetch_url, relpath, deprecated_specfile_name)
            fs = self._get_request(spec_url, allow_fail=True)

        # If we still don't have a result, no go, return empty
        if not fs:
            return

        # Which function and specfile name to use?
        func = (spack.spec.Spec.from_json if spec_url.endswith('json')
                else spack.spec.Spec.from_yaml)

        specfile_contents = codecs.getreader('utf-8')(fs).read()

        # read the spec from the build cache file. All specs in build caches
        # are concrete (as they are built) so we need to mark this spec
        # concrete on read-in.
        spec = func(specfile_contents)
        return MirrorDownload(spec, spec_url, self).to_dict()

    @property
    def name(self):
        return self._name or "<unnamed>"

    def get_profile(self, url_type):
        pass

    def get_fingerprint_links(self):
        return []

    def fetch(self, **kwargs):
        """
        Fetch a spec based on id from a url
        """
        pass

    def set_profile(self, url_type, profile):
        """
        A filesystem mirror does not have a profile (I don't think)
        """
        pass

    def get_access_pair(self, **kwargs):
        pass

    def set_access_pair(self, **kwargs):
        pass

    def get_endpoint_url(self, url_type):
        pass

    def set_endpoint_url(self, **kwargs):
        pass

    def get_access_token(self, url_type):
        pass

    def set_access_token(self, **kwargs):
        pass

    @property
    def fetch_url(self):
        return self._fetch_url

    @property
    def push_url(self):
        if self._push_url is None:
            return self._fetch_url
        return self._push_url

    @fetch_url.setter
    def fetch_url(self, url):
        self._fetch_url["url"] = url
        self._normalize()

    @push_url.setter
    def push_url(self, url):
        self._push_url["url"] = url
        self._normalize()

    def _normalize(self):
        if self._push_url is not None and self._push_url == self._fetch_url:
            self._push_url = None
