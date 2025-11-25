from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
import re

QUESTION_GENERATOR_SYSTEM_PROMPT = """
You are an intelligent question generator. Follow ALL rules exactly:

RULES:
1. Use ONLY the information in the provided CONTEXT. Do NOT add external knowledge.
2. Generate EXACTLY the number of questions requested by the USER. NOT MORE OR LESS.
3. Questions must match the requested difficulty:
   - Easy: direct factual recall
   - Medium: requires basic reasoning or understanding of relationships
   - Hard: requires deeper inference based ONLY on the context
4. Output FORMAT:
   - Numbered list starting from 1
   - ONE question per line
   - No answers, no explanations, no commentary, no filler text
5. If the context does not contain enough information for the requested difficulty, adjust difficulty but NEVER invent facts.
6. After generating EXACTLY the requested number of questions, STOP. Do not add any additional text.

USER REQUEST:
{input}

CONTEXT:
{context}

Generate the questions now.
"""

GRADER_SYSTEM_PROMPT = """
You are an answer grader. Follow ALL rules exactly:

RULES:
1. Use ONLY the supplied CONTEXT. Do NOT use outside knowledge.
2. Compare the user's answer directly to what the CONTEXT states or implies.
3. Output FORMAT (strictly):
   - First line: CORRECT or WRONG
   - Second line: a very brief justification (1–2 sentences)
4. If the CONTEXT does not contain enough information to confirm the user's answer, output WRONG.
5. No additional commentary, no examples, no extra lines.

QUESTION AND USER ANSWER:
{input}

CONTEXT:
{context}

Grade the answer now.
"""

class RAG:
    def __init__(self, model_name, temperature):
        self.model_name = model_name
        self.temperature = temperature
        self.model = Ollama(model=self.model_name, base_url="http://localhost:11434", temperature =self.temperature)
        self.embedding = FastEmbedEmbeddings()
        self.vector_store = Chroma(persist_directory="./sql_chroma_db", embedding_function=self.embedding)

        self.retriever_qg = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10
            },
        )
        
        self.retriever_ca = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.5,
            },
        )
    
    def get_questions(self, number_of_questions, difficulty):
        prompt = PromptTemplate.from_template(QUESTION_GENERATOR_SYSTEM_PROMPT)
        
        document_chain = create_stuff_documents_chain(self.model, prompt)
        chain = create_retrieval_chain(self.retriever_qg, document_chain)

        result = chain.invoke({"input": f"Generate ONLY {number_of_questions} {difficulty} questions."})
        
        pattern = r'^\s*\d+[.)]\s+(.*)$'
        questions = re.findall(pattern, result["answer"], re.MULTILINE)
        
        while len(questions) < number_of_questions:
            questions = self.get_questions(number_of_questions, difficulty)
            
        return questions[:number_of_questions]
        
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

    
