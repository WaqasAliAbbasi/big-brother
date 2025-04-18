# Big Brother

When you need someone looking over you(r credit card emails and sending them to [YNAB](https://www.ynab.com/)).

## How to build image?

```sh
docker build -t big-brother:local .;
source .env;
docker rm -f big-brother;
docker run \
    -e EMAIL_USER=${EMAIL_USER} \
    -e EMAIL_PASSWORD=${EMAIL_PASSWORD} \
    -e YNAB_API_KEY=${YNAB_API_KEY} \
    -e PYTHONUNBUFFERED=1 \
    --restart=always \
    --log-opt max-size=50m \
    -d \
    --name big-brother \
    big-brother:local;
```
