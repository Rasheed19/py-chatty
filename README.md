# py-chatty
py-chatty is a web app for running LLMs locally. It uses [ollama](https://ollama.com/) and [langchain](https://python.langchain.com/docs/introduction/) for setting up the LLM. It uses [py-shiny](https://shiny.posit.co/py/) for the user interface.

It supports both ordinay chat and RAG (chat with your persisted uploaded documents).

## Set up
1. Install ollama from [here](https://ollama.com/). Currently, py-chatty include two LLMs: `deepseek-r1:1.5b` and `llama3.2:1b`; one ollama embedding: `nomic-embed-text`. You can, of course, add new models/embeddings from ollama website and modify `shared/defns.py` to reflect this. It is up to you!

1. Clone this repo and create a virtual environment and activate it. Install the app dependencies by running
    ```
    pip install -r requirements.txt
    ```
1. You might need to start ollama server locally by running the following for one of the downloaded models:
    ```
    ollama run deepseek-r1:1.5b
    ```
1. Start the app. To run ordinary chat, use
    ```
    shiny run chatapp.py
    ```
    and to run in RAG mode, use
    ```
    shiny run ragapp.py
    ```

## What next?
- [x] Add functionality to load other document source (.txt, .docx, web contents, etc)
- [x] Persist uploaded documents in memory and load them when needed
- [ ] Add more parameters to control how LLM works, e.g., temperature, etc
- [ ] Add parameter to control token limits and chat history

## Contribution
Want to contribute? Add your skills or ideas in the contribution section. Whether it's a pull request or an issue... we'd love to hear from you!
