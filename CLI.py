import os
from DocumentsReader import prep_documents
from RAG import RAG

def get_question(model, files, num_questions, difficulty):
    prep_documents(files)
    questions = model.get_questions(num_questions, difficulty)
    
    return [f"Question {i+1} ({difficulty}): {questions[i]}" for i in range(len(questions))]

def check_answers(model, questions, answers):
    return model.check_answers(zip(questions, answers))


class QuestionCLI:
    def __init__(self, model_name_qg, model_name_ac):
        self.files = []
        self.answers = []
        self.questions = []
        self.question_generator_model = RAG(model_name_qg, 0.8)
        self.check_answer_model = RAG(model_name_ac, 0.1)

    # ---------------- INPUT HANDLING ---------------- #
    def ask_for_files(self):
        print("\n=== FILE INPUT ===")
        print("Enter file paths separated by semicolon.")
        files = input("Files: ").strip()

        file_list = [f.strip() for f in files.split(";") if f.strip()]
        missing = [f for f in file_list if not os.path.exists(f)]

        if missing:
            print("\n These files do not exist:")
            for m in missing:
                print("  -", m)
            return self.ask_for_files()

        self.files = file_list
        print("\n✔ Loaded files:")
        for f in file_list:
            print("  -", f)

    def ask_for_question_settings(self):
        print("\n=== QUESTION SETTINGS ===")

        while True:
            try:
                num = int(input("Number of questions: "))
                if num > 0:
                    break
                print("Please enter a positive number.")
            except:
                print("Invalid number.")

        difficulty =  input("Difficulty (Easy / Medium / Hard): ").title().strip()
        while difficulty.lower() not in ["easy", "medium", "hard"]:
            difficulty = input("Incorrect input. Please choose one of the following : Easy , Medium, Hard.").title().strip()

        return num, difficulty

    # ---------------- RUN GENERATION ---------------- #
    def generate_questions(self, num, difficulty):
        print("\nGenerating questions... please wait...\n")
        self.questions = get_question(
            self.question_generator_model, 
            self.files, 
            num, 
            difficulty
        )

        print("=== GENERATED QUESTIONS ===")
        for q in self.questions:
            print("\n" + q)

    def collect_answers(self):
        print("\n=== ANSWER INPUT ===")
        self.answers = []
        for i, q in enumerate(self.questions):
            print(f"\n{q}")
            ans = input("Your answer: ").strip()
            self.answers.append(ans)

    # ---------------- CHECK ANSWERS ---------------- #
    def show_results(self):
        print("\nChecking answers... please wait...\n")
        responses = check_answers(self.check_answer_model, self.questions, self.answers)

        correct_count = sum(1 for r in responses if "correct" in r.lower())
        total = len(responses)

        print("\n=== RESULTS ===")
        for i, r in enumerate(responses):
            print("Feedback for question " + str((i+1)) + ": \n" + r + "\n ---------------\n")

        print(f"\nFinal Score: {correct_count} / {total}")

    # ---------------- RUN LOOP ---------------- #
    def run(self):
        while True:
            print("\n===== Question Generator & Checker (CLI Mode) =====")

            self.ask_for_files()
            num, difficulty = self.ask_for_question_settings()
            self.generate_questions(num, difficulty)
            self.collect_answers()
            self.show_results()
            
            end = input("Do you want to exit? (y/n)").lower().strip()
            while end != "y" and end!="n":
                end = input("Incorrect input. Please choose one of the following: y, or n.")
            if end == "y":
                print("Exiting... Goodbye!")
                break


# --- Run App ---
if __name__ == "__main__":
    model_name_qg = input("Model name for question generation: ")
    model_name_ac = input("Model name for answer correction: ")
    app = QuestionCLI(model_name_qg, model_name_ac)
    app.run()
