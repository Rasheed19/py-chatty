# py-chatty
py-chatty is a web app for running llms locally. It uses [ollama](https://ollama.com/) and [langchain](https://python.langchain.com/docs/introduction/) for setting up the llm. It uses [py-shiny](https://shiny.posit.co/py/) for the user interface.

It supports both ordinay chat and RAG (chat with your upoaded PDF(s) for now!).

## Set up
1. Install ollama from [here](https://ollama.com/). Currently, py-chatty include two llms: `deepseek-r1:1.5b` and `llama3.2:1b`; two ollama embeddings: `nomic-embed-text` and `mxbai-embed-large`. You can, of course, add new models/embeddings from ollama website and modify `shared/defns.py` to reflect this. It is up to you!

1. Clone this repo and create a virtual environment and activate it. Install the app dependencies by running
    ```pip install -r requirements.txt
    ```
1. You might need to start ollama server locally by running for one the downloaded models:
    ```
    ollama run deepseek-r1:1.5b
    ```
1. Start the app by running
    ```
    shiny run chatty.py
    ```

## What next?
1. Add functionality to load other document source (.txt, .docx, web contents, etc)
1. And more ... stay tuned

## Contribution
Want to contribute? Add your skills or ideas in the contribution section. Whether it's a pull request or an issue... we'd love to hear from you!
