# Docker for TextWorld

Dockerfile for running TextWorld - a text-based game generator and extensible sandbox learning environment for training and testing reinforcement learning agents.

## Instructions

```bash
docker pull marccote19/textworld
docker run -p 8888:8888 -it --rm marccote19/textworld
```

Then, in your browser, navigate to the Jupyter notebook's link displayed in your terminal. The link should look like this

```bash
http://127.0.0.1:8888/?token=8d7aaa...e95
```

## Troubleshoot

### bind: address already in use

Try changing the port number published on the host. For instance, to map container's port `8888` (Jupyter's default port) to `9999` on the host, use

```bash
docker run -p 9999:8888 -it --rm marccote19/textworld
```

Then, make sure you modify the Jupyter notebook's link accordingly, i.e.

```bash
http://127.0.0.1:9999/?token=8d7aaa...e95
```
