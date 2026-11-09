git checkout dev
git pull
git checkout stable
git merge dev
git push origin stable
# this updates staging
git push gitlab stable:master
# this updates prod
git push gitlab stable:prod
git checkout dev
