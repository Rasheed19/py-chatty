from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader


# TODO: add functionlaity to load other doc types, eg. docx
def load_pdf(paths: list[str]) -> str:
    text = ""
    for p in paths:
        pdf_reader = PdfReader(p)
        for page in pdf_reader.pages:
            text += page.extract_text()

    return text


# spit text into chunks
def split_text(text: list) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    return chunks


# create embeddings
def create_embedding(model: str) -> OllamaEmbeddings:
    embedding = OllamaEmbeddings(model=model)

    return embedding


# create a database to store embeddings
def create_database(chunks: list, embedding: OllamaEmbeddings) -> Chroma:
    db = Chroma.from_texts(
        texts=chunks, embedding=embedding, collection_name="local-ollama-rag"
    )

    return db


# create a retrieval
def create_retrieval(model: str, db: Chroma) -> tuple[ChatOllama, MultiQueryRetriever]:
    llm = ChatOllama(model=model)

    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to use
        user question to retrieve relevant documents from a vector database.
        By generating multiple perspectives on the user question, your goal is to
        help the user overcome some of the limitations of the distance-based similarity
        search. Provide these alternative questions separated by newlines.
        Original question: {question}""",
    )

    retriever = MultiQueryRetriever.from_llm(
        db.as_retriever(), llm, prompt=QUERY_PROMPT
    )

    return llm, retriever


def create_chain(
    llm: ChatOllama, retriever: MultiQueryRetriever
) -> RunnableSerializable:
    template = """Answer the questuion based ONLY on the following context:
    {context}
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
