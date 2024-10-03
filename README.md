# MultiMediaAI

The objective of this project is to develop a comprehensive solution for identifying suitable songs based on user-provided inputs, including videos, textual descriptions, or music.

## Requirements

- Python 3.10
- Dependencies listed in `requirements.txt`

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/alldbi/MultiMediaAI
    ```

2. **Install dependencies:**

    **Note**: Python 3.10 is required for the installation of the dependencies. If you are using a different version of Python, you can create a virtual environment with Python 3.10 and install the dependencies there.
    ```bash
    cd MultiMediaAI
    pip install -r requirements.txt
    sudo apt-get install poppler-utils
    ```

3. **Connect a device for YouTube:**

    If it's your first time running the application, you need to connect a device for YouTube. Run the following script:
    ```bash
    python setup_yt.py
    ```
    And follow the instructions. You should see a message `Setup finished successfully!` if everything went well.

    If you're unsure whether the device has already been set up, you can still run this script. It won't ask you to connect the device again if it's already set up.

4. **Setup the Suno API:**

    Follow the instructions in the [Suno API Setup Documentation](docs/suno_api_setup.md) to set up the Suno API.

## Running the Gradio App
The Gradio app provides an interactive UI for the backend functionalities.
```bash
python -m src.app
```
Access the application interface via your web browser at `http://127.0.0.1:5002`.

Port 5002 is used by default and can be changed in the `configs/config.py` file.

You can find additional information about settings and the UI in the [Gradio App Documentation](docs/gradio_app.md).

## Running the FastAPI App
The FastAPI app provides API endpoints for backend functionalities.
```bash
python -m src.api
```
Application will run on port 5011.

Port 5011 is used by default and can be changed in the `configs/config.py` file.

You can find additional information about settings and the API endpoints in the [API Documentation](docs/api_docs.md).

## Updating the PyTubeFix Library

To ensure compatibility with the latest changes in YouTube's infrastructure, it is important to regularly update the PyTubeFix library. PyTubeFix is a Python library that fixes issues with downloading audio from YouTube.

To update the PyTubeFix library, you can use the following command:

```bash
pip install --upgrade pytubefix
```

By keeping the PyTubeFix library up to date, you can ensure that your application continues to work seamlessly with YouTube's latest changes and improvements.

## Configuration Files
The project includes several configuration files that control various aspects of the application. These files are located in the `configs` directory.

More information about the configuration files can be found in the [Configuration Files Documentation](docs/configuration_files.md).

## Credentials
You need to provide your API keys  in a `.env` file in the root directory of the project. Also, provide credentials for the AWS S3 bucket where the generated music files will be stored.

Contents of the `.env` file should look like this:
```bash
OPENAI_API_KEY = "sk-XXXXXXXX"
CYANITE_ACCESS_TOKEN = "Bearer XXX"
GRADIO_PASSWORD = "password"

AWS_ACCESS_KEY_ID = ...
AWS_SECRET_ACCESS_KEY = ...
AWS_REGION = ...
AWS_BUCKET = ...

ASSISTANT_ID = ...
ASSISTANT_KNOWLEDGE_FILE_ID = ... # you can find file id in the project settings, storage section
```
*Note*: Generated music will be stored in folder `SUNO_S3_FOLDER` from `configs/config.py` in the specified S3 bucket.# Sff-backend
