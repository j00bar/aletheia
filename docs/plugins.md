---
title: Aletheia Plugins
descriptions: Plugins are used in an Aletheia build pipeline to assemble docs from a foreign source
---

Aletheia plugins fall into several categories: sources, builders, and converters.

## Sources

### Git

* *Plugin name in aletheia.yml:* `git` or `github`
* Arguments:
  * `hostname` (default: `github.com`)
  * `repo`: The path to the git repo on the foreign host (e.g. `j00bar/aletheia`)
  * `branch` (default: `master`): The branch to check out
  * `protocol` (default: `https`): The protocol to use (e.g. `ssh`)
  * `ssh_user`: If `ssh` is used for the protocol, the username to use in connecting
* Output format: Whatever format is in the Git repository

The Git plugin clones another repository containing documentation. Oftentimes, the documentation won't be in the root
directory of the Git repository, in which case you would use the `subdir` plugin to select the directory containing the
docs to graft.

If you are using SSH to connect to Git, you must use key-based authentication and the key needs to be added to a
running SSH agent so as not to prompt for a passphrase.

### Confluence

* *Plugin name in aletheia.yml:* `confluence`
* Arguments:
  * `page_id`: The numeric page identifier for the page in Confluence to graft with its subpages
* Output format: HTML

The Confluence plugin grafts a page and any immediate decendent pages onto the docs tree.

To use the Confluence plugin, you must set environment variables to provide connection information to the plugin:

* `ATLASSIAN_URL`: The base URL to the Confluence site (e.g. `https://acmecorp.atlassian.net/`)
* `ATLASSIAN_API_USERNAME`: The username of an account that can access the page subtree to import
* `ATLASSIAN_API_KEY`: An API key for the account that can access the page subtree to import
* `ATLASSIAN_CLOUD`: Set to a non-empty value if the Confluence site is hosted on Atlassian Cloud

### Google Drive

* *Plugin name in aletheia.yml:* `googledrive`
* Arguments:
  * `folder_id`: The folder ID in Google Drive to export
  * `format` (default: `docx`): The format for exported documents. Supported values are: `epub`, `docx`, `rtf`, and
    `html`
  * `title`: The title for the index page that links to documents in the folder
  * `credentials` (default: `credentials.json`): The path to the file with the Google Drive `credentials.json`
  * `token` (default: `token.pickle`): The path to store the access token for Google Drive
* Output format: Specified by the `format` argument

The Google Drive plugin exports documents contained in a Google Drive folder into the docs tree. An index file will be
autocreated using the provided title. The plugin requires credentials be available on the filesystem to access Google
Drive. Obtain a `credentials.json` file by following [these
steps](https://developers.google.com/workspace/guides/create-credentials), and then run in a Python interpreter:

```python
from aletheia.sources import googledrive
plugin = googledrive.Source(credentials="credentials.json", token="token.pickle")
plugin.get_google_creds(interactive=True)
```

Future executions will refresh and update the token. The `credentials.json` and `token.pickle` should _not_ be
committed to a Git repository.

### Local file paths

* *Plugin name in aletheia.yml:* `local`
* Arguments:
  * `path`: The local file path to import
* Output format: Whatever format is in the local path

The local file path plugin sources documentation from another path on disk, copying the contents into your docs tree.

### Empty

* *Plugin name in aletheia.yml:* `empty`
* Arguments: (none)
* Output format: An empty directory

Every Aletheia pipeline must begin with a source. If you need an empty source, use this.
