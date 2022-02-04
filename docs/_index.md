---
title: Assembling distributed documentation with Aletheia
description: Aletheia collects docs from various configured sources and assembles them into a single tree
---

> _"γνώσεσθε ἀλήθειαν ἀλήθεια ἐλευθερώσει."_
>
> _"Gnosesthe aletheian aletheia eleutherosei."_
>
> "And you will know the truth and the truth shall set you free.

## Why?

Centralized servicing of documentation leads to richer, more useful, more easily referenced sources of truth. Aletheia
was created to solve two problems of centralizing documentation in an organization of teams building services.

First, best practices around documenting services has the documentation of those services living with the code that
they describe. As code evolves, so does the documentation of that code, much the same way we write and commit code with
the tests that verify that code's proper function. However, there is no simple way to centralize the documentation that
lives across several repositories. Aletheia provides that way.

Second, not all teams prefer to write and maintain documentation in the same way. Legacy documentation may exist in
legacy documentation systems. Requiring conformity of all teams to write documentation in the same way in the same
system creates friction and discouragement from writing and updating documentation, and as no team in the history of
ever has had to deal with the problem of having all together too much documentation, eliminating any impediment to
creating and maintaining accurate and comprehensive documentation also is critical to success. Aletheia enables
documentation from different sources to be brought together into a single source.

## How?

A documentation tree assembled by Aletheia begins with a core set of documentation onto which other sources can be
grafted. Aletheia was developed focused on delivering a unified documentation tree for [Hugo](https://gohugo.io/), but
it is not Hugo-specific. It should work with any static-site generation system.

A directory in the content tree can contain a file named `aletheia.yml` which outlines a build pipeline for sourcing,
building, and/or transforming content from another source and grafting it onto the documentation tree at that
directory. The pipeline consists of plugins, serially applied, to create output consummable by the static site
generator.
