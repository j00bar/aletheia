# Aletheia

Aletheia is a tool designed to aggregate sources of documentation and to assimilate them into a single documentation
tree.

For example, let's say you have some core documentation in Hugo, but you also have several GitHub projects where the 
documentation lives with the code. Some of them use Sphinx, some of them use Markdown, and some of them use AsciiDoc. 
Using Aletheia, you can automatically gather those documentation sources, normalize them into Hugo-compatible Markdown,
and assemble a unified tree for Hugo to build.

## Specifying a foreign documentation source

To graft a source of documentation onto your core tree, run:

```
aletheia init path/in/docs/to/graft/onto
```

This will create a no-op `aletheia.yml` file in that path as well as a `.gitignore` file to prevent any assembled
files from polluting your core documentation tree.  The `aletheia.yml` file contains details about the pipeline to 
gather, build, and/or convert the foreign documentation into the format you require.

## Assembling your tree

To assemble a build of your docs, run:

```
aletheia assemble /path/to/write/output
```

This will build your documentation in place.

## Building to export

If you wish to build a copy of the assembled docs for export elsewhere, say, to be served by a webserver like nginx,
you can use the `build` command instead of `assemble`:

```
aletheia build --src /path/to/core/doctree /path/to/build/to
```

This will leave your source tree untouched.

## Things we know we need to do still

1. We need to document the plugins.
2. We need to document how and make it easier to get Google Drive credentials for the `googledrive` plugin.
