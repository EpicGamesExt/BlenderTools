#!/usr/bin/env sh
# install node modules
cd /home/docs

npm install
rm -f -r dist

# abort on errors
set -e


# build
npm run build-linux

#cd dist
#git init
#git add -A
#git commit -m 'deploy'
#git push -f https://${USER}:${GITHUB_TOKEN}@github.com/${ORG}/${REPO}.git master:gh-pages

cd -
