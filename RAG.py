from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
import re

QUESTION_GENERATOR_SYSTEM_PROMPT = """
    <s> [Instructions] 
    You are an intelligent question generator. Your task is to generate questions strictly based on the context provided. You must not ask questions unrelated to the context. Follow these rules carefully:

    Context Awareness: Only use the information provided in the context. Do not introduce outside knowledge or assumptions.

    Question Difficulty: The user will specify the number of questions and the difficulty level: easy, medium, or hard.

    Easy: Simple factual recall questions.

    Medium: Require some reasoning or understanding of relationships.

    Hard: Require deep comprehension, analysis, or inference based on the context.

    Number of Questions: Generate exactly the number of questions requested.

    Clarity: Questions should be clear, concise, and unambiguous.

    Format: Return questions in a numbered list, without answers. ONE QUESTION PER LINE. 

    No Extra Content: Do not include explanations, examples, or unrelated commentary.

    Important: Always ensure every question is fully grounded in the context. If the context does not provide enough information for a question, do not make assumptions—skip or adjust difficulty appropriately.
    [/Instructions] </s>
    [Instructions] 
    User request: {input}
    Context: {context}
    Answer: [/Instructions]
"""

GRADER_SYSTEM_PROMPT = """
<s> [Instructions]
You are an intelligent answer grader. Your task is to evaluate whether the user's answer to the given question is correct strictly based on the provided context.

Context-Based Evaluation:
- You must rely ONLY on the supplied context.
- Do NOT use outside knowledge.
- Do NOT make assumptions beyond what is explicitly stated.

Binary Output Requirement:
- If the user's answer is correct based on the context, start your response with: CORRECT
- If the user's answer is incorrect or not supported by the context, start with: WRONG

Grading Criteria:
- Compare the user's answer to what the context states or implies.
- Minor wording differences are acceptable.
- If the answer contradicts the context or adds unsupported claims, mark WRONG.
- If the context does not contain enough information to support the user's answer, mark WRONG.

Output Format:
- First line: CORRECT or WRONG
- Second line: A brief justification (1–2 sentences max).
- No additional commentary, explanations, or examples.

No Extra Content:
Only use:
1. The context
2. The question
3. The user’s answer

[/Instructions] </s>

[Instructions]
User question and answer: {input}
Context: {context}
Grading:
[/Instructions]
"""

class RAG:
    def __init__(self, model_name, temperature):
        self.model_name = model_name
        self.temperature = temperature
        self.model = OllamaLLM(model=self.model_name, base_url="http://localhost:11434", temperature =self.temperature)
        self.embedding = FastEmbedEmbeddings()
        self.vector_store = Chroma(persist_directory="./sql_chroma_db", embedding_function=self.embedding)

        self.retriever_qg = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": 0.01,
            },
        )
        
        self.retriever_ca = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.4,
            },
        )
    
    def get_questions(self, number_of_questions, difficulty):
        prompt = PromptTemplate.from_template(QUESTION_GENERATOR_SYSTEM_PROMPT)
        
        document_chain = create_stuff_documents_chain(self.model, prompt)
        chain = create_retrieval_chain(self.retriever_qg, document_chain)

        result = chain.invoke({"input": f"Ask {number_of_questions} {difficulty} questions."})
        
        pattern = r'^\s*\d+[.)]\s+(.*)$'
        return re.findall(pattern, result["answer"], re.MULTILINE)
        
    def check_answers(self, user_qa):
        prompt = PromptTemplate.from_template(GRADER_SYSTEM_PROMPT)
        document_chain = create_stuff_documents_chain(self.model, prompt)
        chain = create_retrieval_chain(self.retriever_ca, document_chain)

        feedbacks = []
        for question, answer in user_qa:
            result = chain.invoke({"input": f"Question: {question} \n Answer: {answer}."})
            feedback = result["answer"] + "\n\nSources: \n"
            for doc in result["context"]:
                feedback += doc.metadata["source"] + "\n"
            feedbacks.append(feedback)
        return feedbacks

    
