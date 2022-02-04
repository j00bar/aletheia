---
title: Aletheia Tutorial
description: Getting started using Aletheia
---

To demonstrate the power of Aletheia, let's set up two common use cases: pulling in docs that live in another Github
repository, and pulling in docs that live in Confluence.

Let's imagine that you have a Hugo-based docs site and your content is in `content/en/`.

## Creating a new Aletheia mountpoint

Imagine we have a service called the Foo Service. It has a GitHub repository at
`https://github.com/foocorp/foo-service`, which has documentation about Foo Service in the path `docs` in the
repository. We want to graft those docs onto our site at `/services/foo-service/`.

To start with, we need to make the path for our mountpoint and set up the Aletheia boilerplate:

```shell
mkdir -p content/en/services/foo-service
aletheia init content/en/services/foo-service
```

Running `aletheia init` will put two files into that directory: a `.gitignore` and `aletheia.yml`. The former makes
sure that if you assemble your full documentation tree, the imported content won't be added to your core docs Git
repository. The latter configures the build pipeline.

The boilerplate `aletheia.yml` contains:

```yaml
pipeline:
- empty: {}
- noop: {}
```

This YAML file contains a key `pipeline` that describes our build pipeline. Its value is a list - a series of plugins
that, when run in sequence, should yield a buildable set of docs in the context of Hugo. This boilerplate pipeline
literally does nothing: all pipelines must begin with a [source plugin]({{< ref plugins#Sources >}}), and the `empty`
plugin provides an empty source, while the `noop` plugin performs no operations at all.

What we want instead is:

```yaml
pipeline:
- git:
    repo: "foocorp/foo-service"
    branch: "main"
- subdir:
    path: "docs/"
```

In this pipeline, the source plugin is the [Git](<<{ ref plugins#Git }>>) plugin, which clones a Git repository,
defaulting to one hosted on GitHub. Then we use a [converter plugin](<<{ ref plugins#Converters }>>) called
[subdir](<<{ ref plugins#Subdirectory }>>) to tell Aletheia that the docs are in the `docs/` directory relative to the
git root.

When we run `aletheia assemble` from our Hugo project root directory, Aletheia finds the `aletheia.yml` and executes
its build pipeline, inserting the gathered content in `/content/en/services/foo-service/` such that `hugo serve` should
be able to find it and serve
