# Steps to Change Domain Name

### 1. Open the Nginx Configuration File
You'll need to modify the Nginx configuration file where the current domain names are set.
```bash
sudo nano /etc/nginx/sites-enabled/httpconfig
```

### 2. Update the `server_name` Directives

Locate the `server` blocks within the configuration file and update the `server_name` directive to reflect the new domain name. For example, if you are changing the domain name from `api.sushiandfrenchfries.com` to `newapi.domain.com`, you would modify the relevant section like this:

**Original Configuration:**
```nginx
server {
    server_name api.sushiandfrenchfries.com;
    location / {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/api.sushiandfrenchfries.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/api.sushiandfrenchfries.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
```

**Updated Configuration**: (also delete everything in `server` block that has `# managed by Certbot`)
```nginx
server {
    server_name newapi.domain.com;
    location / {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

```

### 3. Obtain SSL Certificates for the New Domain
If you're using SSL, you'll need to obtain a new SSL certificate for the new domain name. You can use Certbot for this purpose.
```bash
sudo certbot --nginx -d newapi.domain.com
```
This command will automatically update your Nginx configuration to include the correct SSL certificates.

### 4. Test the Nginx Configuration
Before applying the changes, test the Nginx configuration to ensure there are no syntax errors.
```bash
sudo nginx -t
```
If the output indicates that the syntax is correct, proceed to the next step.

### 5. Reload Nginx to Apply Changes
```bash
sudo systemctl reload nginx
```