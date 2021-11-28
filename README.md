# Spack Build Cache (with GitHub) Demo

This is a small demo to show how you can derive an entire spack build cache
on GitHub pages / workflows / packages and then integrate with spack. While
conceptually simply to integrate, the actual integration will require refactoring
how mirrors work (note that it's currently hard coded with S3) so I opted for a demo.

## GitHub Packages Build Cache

Read all about that at [autamus/spack-build-cache](https://github.com/autamus/spack-build-cache).

TLDR: a bunch of workflows use actions from [vsoch/spack-package-action](https://github.com/vsoch/spack-package-action)
to create a matrix of packages, install them, add them to a build cache, deploy to GitHub
packages, and deploy a web interface alongside to explore. [Here is the example interface](https://autamus.io/spack-build-cache/)
for the autamus build cache.

## Usage

The demo is fairly easy to run! Make sure you have spack on your path, and then:

```bash
$ spack python run-demo.py 
==> Warning: Mirror with name autamus-github already exists.
==> Preparing to download ghcr.io/autamus/spack-build-cache/21.11/build_cache/linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack
==> Fetching oras ghcr.io/autamus/spack-build-cache/21.11/build_cache/linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack
==> pull ghcr.io/autamus/spack-build-cache/21.11/build_cache/linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack:latest --output /home/vanessa/Desktop/Code/spack-build-cache-poc
Downloaded 257c65fda48e linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack
Pulled ghcr.io/autamus/spack-build-cache/21.11/build_cache/linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack:latest
Digest: sha256:f57f32693ae091ad69c8b65b8a79b67c50d430ecb9f1b403a5ca6e36760296d9
```

And then the matching binary is in your present working directory. In actual spack
this would be called by a fetched in the Stage class, which sploots it where it needs to be.

```
$ ls
linux-ubuntu20.04-broadwell-gcc-10.3.0-ncurses-6.2-76gsydzye33lca3iqhfijgaxiq46ga53.spack  mirror.py  mirrors  __pycache__  README.md  run-demo.py
```

So, if this looks interesting to you, please use the [run-demo.py](run-demo.py) and 
example [mirrors](mirrors) module and [mirror.py](mirror.py) class to integrate into spack!
