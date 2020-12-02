---
layout: default
folder: ""
---

# Contributing
Having accurate and up to date documentation is important, so that is why we have made it easy to submit changes to our documentation. All the documentation pages are written in markdown, but html tags are supported.

## Editing a Page
To edit an existing page, click the link 'Edit this Page on Github' in the footer of the page you want to edit.

![1]( {{ '/assets/images/contributing/documentation/1.jpg' | relative_url }} )

You will then be prompted to make your own fork of the repository. Click 'Fork this repository'.

![2]( {{ '/assets/images/contributing/documentation/2.jpg' | relative_url }} )

Edit the markdown file and click 'Propose changes'.

![3]( {{ '/assets/images/contributing/documentation/3.jpg' | relative_url }} )

Then create a pull request.

![4]( {{ '/assets/images/contributing/documentation/4.jpg' | relative_url }} )

After your pull request is merged in a new deployment of the site will be made.

## Testing Locally
The documentation site is a static html site that is generated using jekyll. To get up and running with jekyll follow 
their [quickstart guide](https://jekyllrb.com/docs/). Once you have jekyll installed switch to the `/docs` folder and 
start the server by running these commands:
```
cd /docs
bundle exec jekyll serve
```

To force jekyll to regenerate the site files after a file change, you can use:
```
bundle exec jekyll serve --livereload
```

The site should now be available to preview at:

[http://127.0.0.1:4000](http://127.0.0.1:4000)

## Assets
The assets folder contains all the css, javascript, and images for the site. The images folder structure should mirror
the folder structure for the markdown files. Like so:

    .
    ├── ...
    ├── index.md
    ├── send2ue
    ├── ue2rigify
    ├── contributing
    ├── assets
    │    └── images
    │        ├── home
    │        ├── send2ue
    │        ├── ue2rigify
    │        └── contributing
    └── ...

Also each image should be named a number according to the order which they appear on the page. Like so:

    .
    ├── ...
    ├── quickstart
    │   ├── 1.jpg
    │   ├── 2.jpg
    │   └── 3.jpg
    └── ...
    
A image can be referenced into a markdown file by just using the relative path to the `/assets` folder. For example
adding a image to the Send to Unreal quickstart page would look like:
{% raw %}

`![1]( {{ '/assets/images/send2ue/quickstart/1.jpg' | relative_url }} )`
    
{% endraw %}

## Modifying the Sidebar
To edit or add to the side bar, you can edit `/docs/_data/side-nav.yml`. This yaml file contains the titles and the urls
for each of the links in the side bar. The the hierarchy starts with `categories` then `menus` then `submenus`.
    

