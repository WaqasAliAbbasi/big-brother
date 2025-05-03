# Big Brother

When you need someone looking over you(r credit card emails and sending them to [YNAB](https://www.ynab.com/)).

## Development

```sh
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chrome:latest
```

http://localhost:7900/?autoconnect=1&resize=scale&password=secret

## Run

`docker compose up --build -d`