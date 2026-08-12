from langchain_ollama import ChatOllama
from app.rag.retriever import retrieve


SYSTEM_PROMPT = """You are a helpful insurance assistant for GigInsurance.

Answer the user's question using ONLY the policy context provided below.

Rules:
- Do not invent information.
- Do not change numbers or thresholds.
- If the answer is not present in the context, say that you don't have enough information.
- Be concise and easy to understand.
- Use ₹ for monetary amounts.

POLICY CONTEXT:
{context}
"""


question = "What are the conditions for heavy rain coverage?"

# 1. Retrieve relevant policy chunks
chunks = retrieve(question, n_results=3)

if not chunks:
    print("No relevant policy information found.")
    exit()

context = "\n\n---\n\n".join(chunks)

# 2. Start local Qwen
llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0
)

# 3. Give retrieved context to Qwen
prompt = SYSTEM_PROMPT.format(context=context)

response = llm.invoke([
    ("system", prompt),
    ("user", question)
])

print("\nAnswer:\n")
print(response.content)