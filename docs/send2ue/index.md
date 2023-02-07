---
home: true
heroText: Send to Unreal
tagline: A one-click solution for sending data from Blender to Unreal Engine.
actions:
  - text: Quick Start
    link: /introduction/quickstart
features:
- title: Static Meshes
  details: Supports static mesh workflows with lods, mesh origins, and batched exports.
- title: Skeletal Meshes
  details: Bring a skeletal mesh into unreal with its lods and customized lod build settings.
- title: Animation Sequences
  details: Batch export or send individual animations directly to the editor.
- title: Grooms
  details: Batch export or send individual hair systems as alembic files to the editor as groom assets.
footer: Copyright © Epic Games Inc.
---
## Overview

<img :src="$withBase('/images/overview.svg')" alt="overview">


The reason our tool can provide a "one-click" solution for these assets is because it can automatically infer the correct unreal asset type based on just the contents of a single `Export`
collection. That, along with giving the user the ability to customize and share settings templates, allows assets and scenes to be completely configured ahead of time.
A saved file can be opened by an artist and in one-click they can have their assets in unreal engine. The main purpose of this tool
is for rapid iteration and standardization of asset workflows. If you are interested in learning more, please read through the rest of our documentation
starting with our [quickstart guide](./introduction/quickstart)

## Help us document
Our goal is for this documentation to be completely comprehensive so that it can be fully self-serving. If you notice any part of it to be incorrect, unclear, outdated, or missing
information please consider contributing to our documentation.
