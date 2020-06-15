# Aletheia

Aletheia is a tool designed to aggregate sources of documentation and to assimilate them into a single documentation
tree.

For example, let's say you have some core documentation in Hugo, but you also have several GitHub projects where the 
documentation lives with the code. Some of them use Sphinx, some of them use Markdown, and some of them use AsciiDoc. 
Using Aletheia, you can automatically gather those documentation sources, normalize them into Hugo-compatible Markdown,
and assemble a unified tree for Hugo to build.

## Specifying a foreign documentation source

To graft a source of documentation onto your core tree, simply drop a file `aletheia.yml` in an otherwise empty
directory where you want the foreign docs to live in your tree. The `aletheia.yml` file contains details about the
pipeline to gather, build, and/or convert the foreign documentation into the format you require.

## Assembling your tree

To assemble a build of your docs, run:

```
aletheia build --src /path/to/core-docs /path/to/write/output
```
