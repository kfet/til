# Pull new version of existing docker images daily

Put the following in an executable file in `/etc/cron.daily`

`cat /etc/cron.daily/docker-images`:

```
#!/bin/sh

# Pull latest version of all images
docker images | tail -n +2 | grep -v "<none>" | awk -F " " '{print $1":"$2}' | xargs -L1 docker pull

# Clean-up all un-tagged images, we consider those orphaned
docker images | grep "<none>" | awk -F " " '{print $3}' | xargs -L1 docker rmi
```
