from typing import Any

import chromadb
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.defns import OLLAMA_EMBEDDING_NAME, DocSplitterDefaultArgs, Error, FileType


def load_docs(paths: list[str]) -> tuple[list[Document], Error]:
    docs = []

    for p in paths:
        ftype = p.split(".")[-1]

        match ftype:
            case FileType.TXT:
                loader = TextLoader(file_path=p)

            case FileType.CSV:
                loader = CSVLoader(file_path=p)

            case FileType.PDF:
                loader = PyPDFLoader(file_path=p)

            case FileType.DOCX:
                loader = Docx2txtLoader(file_path=p)

            case _:
                return (
                    list(),
                    f"invalid file type, chatty only supports {', '.join(FileType)}",
                )

        docs.extend(loader.load())

    return docs, None


def split_docs(
    docs: list[Document],
    chunk_size: int = DocSplitterDefaultArgs.CHUNK_SIZE,
    chunk_overlap: int = DocSplitterDefaultArgs.CHUNK_OVERLAP,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(docs)

    return chunks


def create_retrieval(
    client: chromadb.ClientAPI,
    collection_name: str,
) -> VectorStoreRetriever:
    db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=OllamaEmbeddings(model=OLLAMA_EMBEDDING_NAME),
    )

    return db.as_retriever()


def validate_splitter_args(arg: Any):
    return isinstance(arg, int) and arg > 0


def create_chain(ollama_model_name: str, retriever: VectorStoreRetriever) -> Runnable:
    # TODO: add more params like temperature, etc; this will also in the ui
    llm = ChatOllama(model=ollama_model_name)

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, just "
        "reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    qa_system_prompt = (
        "You are an assistant for question-answering tasks. Use "
        "the following pieces of retrieved context to answer the "
        "question. If you don't know the answer, just say that you "
        "don't know. Avoid a very long answer and keep the answer "
        "concise."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain
