# Suno API Setup
### Install prerequisites for the Suno API.
Firstly, you need to install Node.js and npm. You can do this by running the following commands:

```
sudo apt install nodejs
sudo apt install npm
```
Check Node version by running `node -v`. \
**Note**: You need to install Node version 15 or higher. Version 20 is suggested. Guide on how to install it on ubuntu: [here](https://medium.com/@nsidana123/before-the-birth-of-of-node-js-15ee9262110c) (note, that you only need to follow Step 1. and first command from Step 2.)

### Install the following packages:
```
pip install git+https://chromium.googlesource.com/external/gyp
pip install six
```

### Clone the repository:
It is recommended to clone the repository in **different** directory than the SFF-Backend repository.
```
git clone https://github.com/gcui-art/suno-api.git
cd suno-api
```
### Configure the Suno API:
Create `.env` file in the `suno-api` directory with the following content:
```
SUNO_COOKIE=<your-cookie>
```
Instructions on how to get the cookie can be found in the [Suno API Documentation](https://github.com/gcui-art/suno-api): 1. Obtain the cookie of your app.suno.ai account

**Important:** You might need to log out and in to get a proper cookie. Ensure your cookie **DOES NOT** start with `_client` (correct cookies start with `_cf`)

### Run locally:
```
npm install
npm run dev
```
Application will run on port 3000.