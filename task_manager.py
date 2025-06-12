# ZenithPlanner/task_manager.py

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from tabulate import tabulate

# --- LLM and Agent Imports ---
from langchain import hub
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_structured_chat_agent
from config import GEMINI_API_KEY


# --- Agent Pydantic Schema ---
class CreateTaskArgs(BaseModel):
    """Input schema for the create_task tool."""
    title: str = Field(description="A concise title for the task.")
    due_time: str | None = Field(description="The deadline in strict ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If no specific time or date is found, this MUST be null.")
    category: str = Field(description="A concise category that best fits the task (e.g., 'Work', 'Health', 'Personal', 'Finance', 'Meeting'). Default to 'Others'.")
    is_recurring: bool = Field(description="true if the task repeats (birthdays, anniversaries, daily/weekly/monthly tasks), otherwise false.", default=False)
    repeat_pattern: str | None = Field(description="Pattern like 'daily', 'weekly', 'monthly', 'yearly'. MUST be 'yearly' for birthdays/anniversaries. null if not recurring.", default=None)
    user_notes: str | None = Field(description="Any extra details from the user. null if none.", default=None)


# --- The Main Agent Class ---
class ZenithAgent:
    def __init__(self, task_manager_instance):
        self.task_manager = task_manager_instance
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.1)
        self.prompt_template = hub.pull("hwchase17/structured-chat-agent")
        print("✅ Self-contained Gemini AI agent loaded in TaskManager.")

    def _create_agent_executor(self, user_id: int, intent: str):
        tools = []
        if intent == 'create':
            def create_task_wrapper(title: str, due_time: str | None, category: str, is_recurring: bool, repeat_pattern: str | None, user_notes: str | None):
                return self.task_manager.create_task_from_agent(
                    user_id, title, due_time, category, is_recurring, repeat_pattern, user_notes
                )
            tools.append(StructuredTool.from_function(
                func=create_task_wrapper, name="create_task", args_schema=CreateTaskArgs,
                description="Use this to create a new task. The current date and time are provided in the prompt for context, use this to calculate the correct absolute date for relative terms like 'today' or 'tomorrow'."
            ))
        elif intent == 'summarize':
            def get_daily_summary_tasks_wrapper():
                return self.task_manager.get_daily_summary_tasks(user_id)
            tools.append(StructuredTool.from_function(
                func=get_daily_summary_tasks_wrapper, name="get_daily_summary_tasks",
                description="Call this to get the user's tasks for a daily summary report."
            ))
        agent = create_structured_chat_agent(self.llm, tools, self.prompt_template)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    def invoke(self, user_input_with_context: str, user_id: int, intent: str):
        try:
            agent_executor = self._create_agent_executor(user_id, intent)
            response = agent_executor.invoke({"input": user_input_with_context, "chat_history": []})
            return response.get('output', "AI Error: No response generated.")
        except Exception as e:
            print(f"❌ Agent Invocation Error: {e}")
            return "AI Error: An unexpected error occurred. Please check the logs."


# --- The Main TaskManager Class ---
class TaskManager:
    def __init__(self, db_connection):
        self.db = db_connection
        self.ist = pytz.timezone('Asia/Kolkata')
        self.agent = ZenithAgent(task_manager_instance=self)

    def add_task_from_natural_language(self, user_input: str, user_id: int) -> str:
        if not user_input: return "❌ Please enter a task description."
        
        # --- THE FIX: Re-introduce time context in an unambiguous format ---
        # This gets the correct current time in IST, whether running locally or on a UTC server.
        now_in_ist = datetime.now(self.ist)
        # Format it clearly for the LLM.
        current_time_str = now_in_ist.strftime("%Y-%m-%d %H:%M:%S %Z") # e.g., "2024-06-13 19:30:00 IST"
        
        prompt_with_context = f"Current time is {current_time_str}. User's request: '{user_input}'"
        # --- END FIX ---

        return self.agent.invoke(prompt_with_context, user_id, intent='create')

    def get_summary_from_agent(self, user_id: int) -> str:
        prompt = """
        Generate a concise and encouraging "Daily Summary".
        Your summary MUST follow these rules:
        1. Create a "Tasks Pending in Next 24 Hours" section. List all pending tasks.
        2. Create a "Tasks Completed Today" section. List all completed tasks.
        3. For each pending task, format it as: `* {Task Title} ({Date} at {Time})`. For example: `* Breakfast (Thu, Jun 13 at 08:00 AM)`.
        4. For each completed task, format it as: `* {Task Title} (at {Time})`.
        5. Both lists must be sorted chronologically (earliest first).
        6. End with a short, motivational message.
        """
        return self.agent.invoke(prompt, user_id, intent='summarize')

    def list_prioritized_tasks(self, user_id: int) -> list:
        tasks = self.db.get_tasks(user_id=user_id, completed=False)
        now_ist = datetime.now(self.ist)
        one_day_from_now = now_ist + timedelta(days=1)
        prioritized_tasks = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict.get('due_time'):
                due_time_obj = task_dict['due_time'].astimezone(self.ist)
                if due_time_obj <= one_day_from_now:
                    task_dict['time_left'] = due_time_obj - now_ist
                    prioritized_tasks.append(task_dict)
            else:
                prioritized_tasks.append(task_dict)
        far_future_date = datetime.max.replace(tzinfo=pytz.UTC)
        prioritized_tasks.sort(key=lambda x: x.get('due_time') or far_future_date)
        return prioritized_tasks

    def get_countdown_events(self, user_id: int) -> list:
        tasks = self.db.get_tasks(user_id=user_id, completed=False)
        now_ist = datetime.now(self.ist)
        one_day_from_now = now_ist + timedelta(days=1)
        countdown_tasks = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict.get('due_time'):
                due_time_obj = task_dict['due_time'].astimezone(self.ist)
                if due_time_obj > one_day_from_now:
                    task_dict['time_left'] = due_time_obj - now_ist
                    countdown_tasks.append(task_dict)
        countdown_tasks.sort(key=lambda x: x['due_time'])
        return countdown_tasks

    def create_task_from_agent(self, user_id: int, title: str, due_time: str | None, category: str, is_recurring: bool, repeat_pattern: str | None, user_notes: str | None) -> str:
        task_data = locals()
        task_data.pop('self'); task_data.pop('user_id')
        if task_data.get('due_time'):
            try:
                due_time_obj = datetime.fromisoformat(task_data['due_time']).astimezone(self.ist)
                task_data['due_time'] = due_time_obj.isoformat()
            except (ValueError, TypeError):
                return f"Error: The AI provided a due_time '{task_data['due_time']}' that could not be understood."
        self.db.add_task(task_data, user_id)
        return f"Successfully created task titled '{title}'."

    def get_daily_summary_tasks(self, user_id: int) -> str:
        all_tasks = self.db.get_tasks(user_id=user_id, completed=None)
        if not all_tasks: return "The user has no tasks at all."
        
        now_ist = datetime.now(self.ist)
        one_day_from_now = now_ist + timedelta(days=1)
        today_start = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        
        pending_next_24h = []
        completed_today = []

        for task in all_tasks:
            if not task.get('due_time'): continue
            due_time = task['due_time'].astimezone(self.ist)
            if not task['is_completed'] and (now_ist <= due_time < one_day_from_now):
                pending_next_24h.append(task)
            elif task['is_completed'] and (today_start <= due_time < now_ist):
                 completed_today.append(task)

        pending_next_24h.sort(key=lambda x: x['due_time'])
        completed_today.sort(key=lambda x: x['due_time'])
        
        pending_data = []
        for task in pending_next_24h:
            due_str = task['due_time'].astimezone(self.ist).strftime('%a, %b %d at %I:%M %p')
            pending_data.append([task['title'], "Pending", due_str])
        
        completed_data = []
        for task in completed_today:
            due_str = task['due_time'].astimezone(self.ist).strftime('%I:%M %p')
            completed_data.append([task['title'], "Completed", due_str])

        pending_table = "No tasks pending in the next 24 hours."
        if pending_data:
            pending_table = "Pending Tasks:\n" + tabulate(pending_data, headers=["Title", "Status", "Due"], tablefmt="grid")

        completed_table = "No tasks completed today."
        if completed_data:
            completed_table = "Completed Tasks:\n" + tabulate(completed_data, headers=["Title", "Status", "Time"], tablefmt="grid")
            
        return f"{pending_table}\n\n{completed_table}"

    def mark_task_complete(self, task_id: int, user_id: int):
        self.db.update_task_status(task_id, user_id, is_completed=True)
    
    def delete_task(self, task_id: int, user_id: int):
        self.db.delete_task(task_id, user_id)