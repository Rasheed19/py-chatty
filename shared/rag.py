from typing import Any

import chromadb
from langchain.prompts import ChatPromptTemplate
from langchain.retrievers.multi_query import DEFAULT_QUERY_PROMPT, MultiQueryRetriever
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.defns import OLLAMA_EMBEDDING_NAME, DocSplitterDefaultArgs, Error, FileType

# from langchain.chains import ConversationalRetrievalChain
# from langchain.memory import ConversationBufferMemory


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
    model: str,
    client: chromadb.ClientAPI,
    collection_name: str,
) -> tuple[ChatOllama, MultiQueryRetriever]:
    db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=OllamaEmbeddings(model=OLLAMA_EMBEDDING_NAME),
    )

    llm = ChatOllama(model=model)

    # maybe customize params of as_retriever??
    retriever = MultiQueryRetriever.from_llm(
        db.as_retriever(), llm, prompt=DEFAULT_QUERY_PROMPT
    )

    return llm, retriever


def validate_splitter_args(arg: Any):
    return isinstance(arg, int) and arg > 0


def create_chain(
    llm: ChatOllama, retriever: MultiQueryRetriever
) -> RunnableSerializable:
    # TODO: update this prompt, use the template in the youtube video
    # TODO: update this to answer other general question
    # template = """Instruction:
    # You are an AI language model that must answer questions only based on the given context.
    # If the answer is not found in the provided context, respond with: "I don't know based on the given context."
    # Do not generate answers outside the given information, do not make assumptions, and do not provide external knowledge.

    # Context:
    # {context}

    # User Question:
    # {question}

    # Answer:
    # """

    template = """Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Use three sentences maximum and keep the answer as concise as possible.
    Always say "thanks for asking!" at the end of the answer.

    {context}

    Question: {question}

    Helpful Answer:"""

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
