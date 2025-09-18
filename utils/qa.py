from ollama import Client

client = Client()

def ask_ollama(context, question):
    prompt = f"""
    You are a financial assistant.
    Use the following financial document content to answer the question.

    Document Content:
    {context}

    Question: {question}
    """
    response = client.chat(model="smollm2:135m", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]
