import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from DocumentsReader import prep_documents
from RAG import RAG

# ------------------- BACKEND HELPERS  ------------------- #

def get_question(model, files, num_questions, difficulty):
    prep_documents(files)
    questions = model.get_questions(num_questions, difficulty)
    return [f"Question {i+1} ({difficulty}): {questions[i]}" for i in range(len(questions))]


def check_answers(model, questions, answers):
    return model.check_answers(zip(questions, answers))

# ----------------------------- MAIN TK APP -------------------------------- #

class QuestionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Question Generator & Checker")
        self.geometry("900x600")

        # shared state
        self.files = []
        self.questions = []
        self.answers = []
        self.responses = []
        self.num_questions = 0
        self.difficulty = "Easy"
        self.model_name_qg = ""
        self.model_name_ac = ""
        self.question_generator_model = None
        self.check_answer_model = None
        self.correct_count = 0
        self.total = 0

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ConfigFrame, QuestionFrame, ResultFrame):
            frame = F(parent=container, app=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConfigFrame")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    def start_new_session(self):
        self.files = []
        self.questions = []
        self.answers = []
        self.responses = []
        self.num_questions = 0
        self.difficulty = "Easy"
        self.correct_count = 0
        self.total = 0

        cfg = self.frames["ConfigFrame"]
        qf = self.frames["QuestionFrame"]
        rf = self.frames["ResultFrame"]
        cfg.reset()
        qf.reset()
        rf.reset()

        self.show_frame("ConfigFrame")


# --------------------------- CONFIGURATION SCREEN ------------------------- #

class ConfigFrame(tk.Frame):
    def __init__(self, parent, app: QuestionApp):
        super().__init__(parent)
        self.app = app

        self.selected_files = []

        # Layout
        title = tk.Label(self, text="Configuration", font=("Arial", 20, "bold"))
        title.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(fill="x", padx=20, pady=10)

        # Model names
        tk.Label(form_frame, text="Model name (Question Generation):").grid(row=0, column=0, sticky="w", pady=5)
        self.qg_entry = tk.Entry(form_frame, width=40)
        self.qg_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Model name (Answer Correction):").grid(row=1, column=0, sticky="w", pady=5)
        self.ac_entry = tk.Entry(form_frame, width=40)
        self.ac_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Number of questions
        tk.Label(form_frame, text="Number of questions:").grid(row=2, column=0, sticky="w", pady=5)
        self.num_questions_var = tk.StringVar(value="5")
        self.num_questions_entry = tk.Entry(form_frame, textvariable=self.num_questions_var, width=10)
        self.num_questions_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Difficulty
        tk.Label(form_frame, text="Difficulty:").grid(row=3, column=0, sticky="w", pady=5)
        self.difficulty_var = tk.StringVar(value="Easy")
        self.difficulty_combo = ttk.Combobox(
            form_frame,
            textvariable=self.difficulty_var,
            values=["Easy", "Medium", "Hard"],
            state="readonly",
            width=10
        )
        self.difficulty_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # File selection
        file_frame = tk.LabelFrame(self, text="Files")
        file_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.file_listbox = tk.Listbox(file_frame, height=8)
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        scrollbar = tk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        self.browse_btn = tk.Button(btn_frame, text="Browse Files", command=self.browse_files)
        self.browse_btn.grid(row=0, column=0, padx=5)

        self.generate_btn = tk.Button(btn_frame, text="Generate Questions", command=self.on_generate_questions)
        self.generate_btn.grid(row=0, column=1, padx=5)

        # Status label for loading message
        self.status_label = tk.Label(self, text="", fg="blue", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def browse_files(self):
        filepaths = filedialog.askopenfilenames(title="Select documents")
        if filepaths:
            self.selected_files = list(filepaths)
            self.file_listbox.delete(0, tk.END)
            for f in self.selected_files:
                self.file_listbox.insert(tk.END, f)

    def on_generate_questions(self):
        # Validation
        model_name_qg = self.qg_entry.get().strip()
        model_name_ac = self.ac_entry.get().strip()
        if not model_name_qg or not model_name_ac:
            messagebox.showerror("Error", "Please provide both model names.")
            return

        if not self.selected_files:
            messagebox.showerror("Error", "Please select at least one file.")
            return

        try:
            num_questions = int(self.num_questions_var.get())
            if num_questions <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Number of questions must be a positive integer.")
            return

        difficulty = self.difficulty_var.get().strip().title()
        if difficulty.lower() not in ["easy", "medium", "hard"]:
            messagebox.showerror("Error", "Difficulty must be Easy, Medium, or Hard.")
            return

        # Check file existence
        missing = [f for f in self.selected_files if not os.path.exists(f)]
        if missing:
            messagebox.showerror(
                "Missing files",
                "These files do not exist:\n" + "\n".join(missing)
            )
            return

        # Store state in app
        self.app.model_name_qg = model_name_qg
        self.app.model_name_ac = model_name_ac
        self.app.files = self.selected_files
        self.app.num_questions = num_questions
        self.app.difficulty = difficulty

        # Instantiate models
        try:
            self.app.question_generator_model = RAG(model_name_qg, 0.4)
            self.app.check_answer_model = RAG(model_name_ac, 0.0)
        except Exception as e:
            messagebox.showerror("Model Error", f"Failed to initialize models:\n{e}")
            return

        # Disable button & show message, then run generation async
        self.generate_btn.config(state="disabled")
        self.status_label.config(text="Generating questions... please wait.")
        self.after(100, self.generate_questions_async)

    def generate_questions_async(self):
        try:
            self.app.questions = get_question(
                self.app.question_generator_model,
                self.app.files,
                self.app.num_questions,
                self.app.difficulty
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate questions:\n{e}")
            self.app.questions = []
        finally:
            # Restore UI
            self.generate_btn.config(state="normal")
            self.status_label.config(text="")

        # Load questions into QuestionFrame and switch screen if successful
        if self.app.questions:
            q_frame: QuestionFrame = self.app.frames["QuestionFrame"]
            q_frame.load_questions()
            self.app.show_frame("QuestionFrame")

    def reset(self):
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.qg_entry.delete(0, tk.END)
        self.ac_entry.delete(0, tk.END)
        self.num_questions_var.set("5")
        self.difficulty_var.set("Easy")
        self.status_label.config(text="")
        self.generate_btn.config(state="normal")


# ----------------------------- Q&A SCREEN --------------------------------- #

class QuestionFrame(tk.Frame):
    def __init__(self, parent, app: QuestionApp):
        super().__init__(parent)
        self.app = app
        self.answer_widgets = []

        title = tk.Label(self, text="Questions & Answers", font=("Arial", 20, "bold"))
        title.pack(pady=10)

        # Scrollable area for questions
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(outer_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        self.submit_btn = tk.Button(btn_frame, text="Submit Answers", command=self.on_submit_answers)
        self.submit_btn.grid(row=0, column=0, padx=5)

        self.back_btn = tk.Button(btn_frame, text="Back to Config", command=self.on_back)
        self.back_btn.grid(row=0, column=1, padx=5)

        # Status label for checking answers
        self.status_label = tk.Label(self, text="", fg="blue", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def load_questions(self):
        # Clear previous content
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.answer_widgets = []

        if not self.app.questions:
            tk.Label(self.inner_frame, text="No questions generated.", font=("Arial", 12)).pack(pady=10)
            return

        for idx, q in enumerate(self.app.questions):
            q_label = tk.Label(self.inner_frame, text=q, wraplength=800, justify="left", anchor="w")
            q_label.pack(fill="x", pady=(5, 0))

            ans_text = tk.Text(self.inner_frame, height=3, wrap="word")
            ans_text.pack(fill="x", pady=(0, 10))
            self.answer_widgets.append(ans_text)

    def on_submit_answers(self):
        answers = []
        for w in self.answer_widgets:
            text = w.get("1.0", tk.END).strip()
            answers.append(text)

        if any(a == "" for a in answers):
            if not messagebox.askyesno("Confirm", "Some answers are empty. Submit anyway?"):
                return

        self.app.answers = answers

        # Disable button + show loading message
        self.submit_btn.config(state="disabled")
        self.status_label.config(text="Checking answers... please wait.")
        self.after(100, self.check_answers_async)

    def check_answers_async(self):
        try:
            responses = check_answers(
                self.app.check_answer_model,
                self.app.questions,
                self.app.answers
            )
            self.app.responses = list(responses)
            self.app.correct_count = sum(1 for r in self.app.responses if "CORRECT" in r)
            self.app.total = len(self.app.responses)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check answers:\n{e}")
            self.app.responses = []
            self.app.correct_count = 0
            self.app.total = 0
        finally:
            # Restore UI
            self.submit_btn.config(state="normal")
            self.status_label.config(text="")

        # Load results screen
        result_frame: ResultFrame = self.app.frames["ResultFrame"]
        result_frame.load_results()
        self.app.show_frame("ResultFrame")

    def on_back(self):
        self.app.show_frame("ConfigFrame")

    def reset(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.answer_widgets = []
        self.status_label.config(text="")
        self.submit_btn.config(state="normal")


# ----------------------------- RESULT SCREEN ------------------------------ #

class ResultFrame(tk.Frame):
    def __init__(self, parent, app: QuestionApp):
        super().__init__(parent)
        self.app = app

        title = tk.Label(self, text="Results & Feedback", font=("Arial", 20, "bold"))
        title.pack(pady=10)

        self.score_label = tk.Label(self, text="", font=("Arial", 14, "bold"))
        self.score_label.pack(pady=5)

        # Feedback area
        feedback_frame = tk.Frame(self)
        feedback_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.feedback_text = tk.Text(feedback_frame, wrap="word")
        self.feedback_text.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        scrollbar = tk.Scrollbar(feedback_frame, orient="vertical", command=self.feedback_text.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.feedback_text.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        self.new_session_btn = tk.Button(btn_frame, text="New Session", command=self.app.start_new_session)
        self.new_session_btn.grid(row=0, column=0, padx=5)

        self.exit_btn = tk.Button(btn_frame, text="Exit", command=self.app.destroy)
        self.exit_btn.grid(row=0, column=1, padx=5)

    def load_results(self):
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", tk.END)

        if not self.app.responses:
            self.score_label.config(text="No responses.")
            self.feedback_text.insert(tk.END, "No feedback available.\n")
        else:
            self.score_label.config(
                text=f"Final Score: {self.app.correct_count} / {self.app.total}"
            )
            for i, r in enumerate(self.app.responses):
                self.feedback_text.insert(
                    tk.END,
                    f"Feedback for question {i+1}:\n{r}\n---------------\n\n"
                )

        self.feedback_text.config(state="disabled")

    def reset(self):
        self.score_label.config(text="")
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", tk.END)
        self.feedback_text.config(state="disabled")

# ------------------------------- RUN APP ---------------------------------- #

if __name__ == "__main__":
    app = QuestionApp()
    app.mainloop()
