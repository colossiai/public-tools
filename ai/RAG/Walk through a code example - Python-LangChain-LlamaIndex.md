# Walk through a code example (Python / LangChain / LlamaIndex)


I'll show a **minimal RAG example** using **Python + LangChain** because it's the most common starting point.
Then I’ll show the **equivalent structure in LlamaIndex** so you can compare.

The example will:

1. Load documents
2. Create embeddings
3. Store in vector DB
4. Retrieve relevant chunks
5. Send to LLM for answer

---

# 1. Minimal RAG with Python + LangChain

## Install dependencies

```bash
pip install langchain langchain-openai faiss-cpu pypdf
```

Components used:

* LLM: OpenAI API
* Vector DB: FAISS
* Framework: LangChain

---

# 2. Load and chunk documents

Suppose we have a PDF manual.

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = PyPDFLoader("manual.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

docs = splitter.split_documents(documents)
```

Why chunk?

LLMs cannot read huge documents at once.
Chunks make retrieval more precise.

---

# 3. Create embeddings

Embeddings convert text → vectors.

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
```

Example:

```
"RAG improves LLM accuracy"
→ [0.21, -0.77, 0.33, ...]
```

These vectors allow **semantic search**.

---

# 4. Store in vector database

```python
from langchain.vectorstores import FAISS

vector_db = FAISS.from_documents(
    docs,
    embeddings
)
```

Now your documents are stored as vectors.

---

# 5. Create retriever

Retriever finds the most relevant chunks.

```python
retriever = vector_db.as_retriever(
    search_kwargs={"k": 3}
)
```

Meaning:

```
User question
   ↓
Top 3 similar chunks returned
```

---

# 6. Build the RAG chain

```python
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever
)
```

---

# 7. Ask a question

```python
response = qa.invoke(
    {"query": "What is retrieval augmented generation?"}
)

print(response["result"])
```

Pipeline executed internally:

```
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
Retrieve chunks
   ↓
Prompt + Context
   ↓
LLM generates answer
```

---

# Prompt sent to the LLM

Something like:

```
Use the following context to answer the question.

Context:
[chunk1]
[chunk2]
[chunk3]

Question:
What is retrieval augmented generation?

Answer:
```

---

# 8. Full minimal RAG script

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA

loader = PyPDFLoader("manual.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()

vector_db = FAISS.from_documents(docs, embeddings)

retriever = vector_db.as_retriever(search_kwargs={"k": 3})

llm = ChatOpenAI(model="gpt-4o-mini")

qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

print(qa.invoke({"query": "Explain RAG"}))
```

---

# 9. Same idea using LlamaIndex

LlamaIndex is more **RAG-focused** than LangChain.

Install:

```bash
pip install llama-index
```

Example:

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./docs").load_data()

index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()

response = query_engine.query(
    "What is retrieval augmented generation?"
)

print(response)
```

Much simpler because LlamaIndex hides many steps.

---

# LangChain vs LlamaIndex

| Feature    | LangChain              | LlamaIndex           |
| ---------- | ---------------------- | -------------------- |
| Purpose    | LLM workflow framework | RAG / data framework |
| Complexity | Higher                 | Lower                |
| Control    | Very flexible          | Opinionated          |
| Best for   | Agents / pipelines     | Knowledge Q&A        |

---

# Minimal RAG architecture (code version)

```
Documents
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector DB
   ↓
Retriever
   ↓
Prompt + Context
   ↓
LLM
   ↓
Answer
```

---

If you'd like, I can also show:

* **Production-grade RAG architecture (used by companies)**
* **How to build RAG without LangChain (pure Python)** — much cleaner
* **How high-performance RAG systems work (OpenAI / Perplexity style)**
* **How RAG is implemented in low-latency systems (relevant for trading-style infra)**.
