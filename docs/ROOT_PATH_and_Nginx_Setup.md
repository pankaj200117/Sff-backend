## ROOT_PATH

### Description
This parameter sets the root path for your applications. It allows you to specify a base URL under which your applications will be accessible. This is useful when you need to deploy your apps under a specific endpoint, such as `/beta`.



### Example
If you want to access your applications from the `/beta` endpoint, while running the main application on port 5010 and the beta application on port 5011,
you should set `ROOT_PATH = "/beta"` in the `config.py` file and change Nginx configuration accordingly.

You can change `GRADIO_ROOT_PATH` for gradio application or `API_ROOT_PATH` for api application in the `config.py` file.

### Nginx Configuration

To proxy requests to the appropriate application based on the root path, you can configure Nginx as shown below:

```nginx
server {
    server_name your_project_link.com;

    location / {
        proxy_pass http://127.0.0.1:5010;
    }

    location /beta {
        proxy_pass http://127.0.0.1:5011;
    }
}
```
Note: if you don't want to use a different root path, you should set `ROOT_PATH = ""`(not `"/"`) in the `config.py` file.