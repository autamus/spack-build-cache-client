#!/usr/bin/env spack-python

# This is a proof of concept to use GitHub packages as a build cache.
# The current spack mirrors model is hard coded for S3 so here I've imagined
# how I would go about it. We have a hard coded spec.json to look for
# that is known to be in the cache

import spack.config
import spack.mirror
import spack.fetch_strategy as fetch
from spack.util.spack_yaml import syaml_dict

import llnl.util.tty as tty
import spack.util.url as url_util
import re
import os
import sys

sys.path.insert(0, os.path.dirname("run-demo.py"))

# This emulates a set of Mirror classes. We don't currently have them because it's hard
# coded for AWS. So instead of Mirror you would do get_mirror and return a mirror
# class based on the kind of mirror provided.
from mirrors import MirrorGHCR
from mirror import MirrorCollection

# Additional functions for mirrors. If we have more than one there should be
# a function to add credentials


def get_mirror_credentials(args):
    """
    Given spack mirror command args, get credentials for a supported mirror
    """
    url = url_util.format(args.url)
    mirror_data = url

    # Is the user requesting s3 or ghcr?
    s3_values = ["s3_access_key_id", "s3_access_token", "s3_profile"]
    ghcr_values = ["ghcr_token", "ghcr_username", "ghcr_packages_org"]

    # The credentials are for an s3 mirror
    if any(v for v in s3_values if getattr(args, v, None)) or url.startswith("s3"):
        mirror_data = {
            "url": url,
            "access_pair": (args.s3_access_key_id, args.s3_access_key_secret),
            "access_token": args.s3_access_token,
            "profile": args.s3_profile,
            "endpoint_url": args.s3_endpoint_url,
        }
        return {"fetch": mirror_data, "push": mirror_data, "type": "s3"}

    # The credentials / url are for ghcr
    if any(v for v in ghcr_values if getattr(args, v, None)) or url.startswith("ghcr"):
        # Should be provided ghcr.io/<org>/<repo>
        match = re.match("ghcr://(?P<org>.*)/(?P<repo>.*)", args.url)
        if not match:
            tty.die("%s does not match ghcr://<org>/<repo>" % args.url)

        # Keys index
        org, repo = match.groups()
        mirror_data = {
            "url": "https://%s.github.io/%s" % (org, repo),
            "oras": "ghcr.io/%s/%s" % (org, repo),
            "ghcr_token": args.ghcr_token,
            "ghcr_username": args.ghcr_username,
            "ghcr_packages_org": args.ghcr_packages_org,
        }
        return {"fetch": mirror_data, "push": mirror_data, "type": "ghcr"}

    # A base or filesystem mirror
    return {"fetch": mirror_data, "push": mirror_data, "type": "base"}


def add(name, url, scope, args={}):
    """
    Add a named mirror in the given scope
    """
    mirrors = spack.config.get("mirrors", scope=scope)
    if not mirrors:
        mirrors = syaml_dict()

    if name in mirrors:
        tty.warn("Mirror with name %s already exists." % name)
        return

    items = [(n, u) for n, u in mirrors.items()]
    mirror_data = get_mirror_credentials(args)

    items.insert(0, (name, mirror_data))
    mirrors = syaml_dict(items)
    spack.config.set("mirrors", mirrors, scope=scope)


# This is only here for visibility, it belongs inside a fetcher.
def oras_fetch(url, dest=None):
    """
    Fetch a binary cache entry with oras
    """
    if dest == None:
        dest = os.getcwd()
    import spack.bootstrap

    tty.msg("Fetching oras {0}".format(url))

    with spack.bootstrap.ensure_bootstrap_configuration():
        spec = spack.spec.Spec("oras")
        spack.bootstrap.ensure_executables_in_path_or_raise(
            ["oras"], abstract_spec=spec
        )
        oras = spack.util.executable.which("oras")
        cmd = ["pull", url + ":latest", "--output", dest]
        tty.msg(" ".join(cmd))
        oras(*cmd)
        return dest


# This could also be added as a function to a URL Fetcher
@fetch.fetcher
class OrasFetcher(fetch.URLFetchStrategy):
    """
    An oras fetcher bootstraps oras to perform a fetch
    """

    def _oras_fetch(self, url):
        return oras_fetch(url)

    @fetch._needs_stage
    def fetch(self):
        for url in self.candidate_urls:

            # This would fit into the current URLFetchstategy.fetch
            # you would want to check for prefix ghcr or oras first
            self._oras_fetch(url)


def main():

    # Create dummy args
    class Args:
        url = "ghcr://autamus/spack-build-cache"

        def __getattr__(self, name):
            return None

    args = Args()

    # Add the mirror with dummy args
    add("autamus-github", "ghcr://autamus/spack-build-cache", scope=None, args=args)

    # Get all of our mirrors!
    mirrors = MirrorCollection()
    for name in mirrors:

        # Only care to demo autamus-github
        if name == "autamus-github":
            mirror = mirrors[name]

            # This is a spec.json we know to exist in the mirror.
            # The GHCR build cache does not currently support yaml (it is deprecated)
            spec_json = "linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spec.json"

            # The mirror download is the to_dict() result of a new class, MirrorDownload, that might be useful to have
            mirror_download = mirror.fetch_spec(spec_json)

            # a set of these objects is passed between installer.py and binary_distribution.py
            # Until we get into the part to generate a url for Stage, we do that by modifying the fetcher.
            # Here we will just use a custom fetcher that would be run in stage to pop the binary .spack
            # archive where it needs to be. We get the final url again from the mirror
            url = mirror_download["mirror"].get_download_tarball(mirror_download)
            tty.info("Preparing to download %s" % url)
            oras_fetch(url)


if __name__ == "__main__":
    main()
