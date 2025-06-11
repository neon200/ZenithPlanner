# ZenithPlanner/task_manager.py

from datetime import datetime, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz
from llm_utils import parse_task_with_gemini

class TaskManager:
    """
    The central business logic unit of ZenithPlanner.
    It connects the UI, the database, and the LLM.
    """
    def __init__(self, db_connection):
        """Initializes the TaskManager with a database connection instance."""
        self.db = db_connection
        # Always use IST timezone
        self.ist = pytz.timezone('Asia/Kolkata')

    def add_task_from_natural_language(self, user_input: str, user_id: int) -> str:
        """
        Processes natural language input, parses it with the LLM, and adds it to the database.
        """
        if not user_input:
            return "❌ Please enter a task description."

        parsed_data = parse_task_with_gemini(user_input)
        
        if "error" in parsed_data:
            return f"❌ AI Error: {parsed_data['error']}"
        
        if not parsed_data.get("title"):
            return "❌ AI Error: The AI could not determine a title for your task. Please try rephrasing."

        # Ensure due_time is properly timezone-aware for IST
        if parsed_data.get('due_time'):
            try:
                # Parse the time string
                due_time_obj = datetime.fromisoformat(parsed_data['due_time'])
                
                # If it's naive (no timezone), assume it's IST
                if due_time_obj.tzinfo is None:
                    due_time_obj = self.ist.localize(due_time_obj)
                else:
                    # Convert to IST if it's in a different timezone
                    due_time_obj = due_time_obj.astimezone(self.ist)
                
                # Update the parsed data with timezone-aware datetime
                parsed_data['due_time'] = due_time_obj.isoformat()
                
            except Exception as e:
                print(f"⚠️ Error processing due_time: {e}")
                # If there's an error, remove the due_time rather than storing invalid data
                parsed_data['due_time'] = None

        self.db.add_task(parsed_data, user_id)
        
        # Create a user-friendly confirmation message
        title = parsed_data.get('title')
        due_info = ""
        if parsed_data.get('due_time'):
            try:
                due_obj = datetime.fromisoformat(parsed_data['due_time'].replace('Z', '+00:00'))
                if due_obj.tzinfo:
                    due_obj = due_obj.astimezone(self.ist)
                due_info = f" scheduled for {due_obj.strftime('%A, %B %d at %I:%M %p IST')}"
            except:
                pass
        
        return f"✅ Task '{title}'{due_info} added successfully."

    def list_prioritized_tasks(self, user_id: int) -> list:
        """
        Retrieves all incomplete tasks for a user and sorts them based on urgency.
        All times are handled in IST.
        """
        tasks = self.db.get_tasks(user_id=user_id, completed=False)
        now_ist = datetime.now(self.ist)
        
        due_tasks = []
        no_due_date_tasks = []
        
        for task in tasks:
            task_dict = dict(task)
            if self._is_event(task_dict):
                continue
            
            if task_dict.get('due_time'):
                try:
                    due_time_obj = task_dict['due_time']
                    
                    # Ensure the datetime is timezone-aware and in IST
                    if due_time_obj.tzinfo is None:
                        due_time_obj = self.ist.localize(due_time_obj)
                    else:
                        due_time_obj = due_time_obj.astimezone(self.ist)

                    # Handle yearly recurring events
                    if self._is_yearly_recurring_event(task_dict) and due_time_obj < now_ist:
                        next_year = due_time_obj + relativedelta(years=1)
                        task_dict['due_time'] = next_year
                        self.db.update_task_due_time(task_dict['id'], user_id, next_year.isoformat())
                        due_time_obj = next_year
                    
                    task_dict['time_left'] = due_time_obj - now_ist
                    due_tasks.append(task_dict)
                    
                except (parser.ParserError, TypeError, ValueError) as e:
                    print(f"⚠️ Error parsing task due_time for task {task_dict.get('id', 'unknown')}: {e}")
                    no_due_date_tasks.append(task_dict)
            else:
                no_due_date_tasks.append(task_dict)
        
        # Sort by urgency (least time left first)
        due_tasks.sort(key=lambda x: x['time_left'])
        return due_tasks + no_due_date_tasks

    def _is_yearly_recurring_event(self, task_dict: dict) -> bool:
        """Determines if a task is a yearly recurring event like birthdays."""
        title_lower = task_dict.get('title', '').lower()
        category_lower = task_dict.get('category', '').lower()
        birthday_keywords = ['birthday', 'bday', 'b-day', 'born']
        yearly_keywords = ['anniversary', 'wedding', 'graduation day']
        
        return any(keyword in title_lower for keyword in birthday_keywords + yearly_keywords) or \
               'personal' in category_lower and any(keyword in title_lower for keyword in birthday_keywords)

    def _is_event(self, task_dict: dict) -> bool:
        """Determines if a task is an event for countdown purposes."""
        title_lower = task_dict.get('title', '').lower()
        category_lower = task_dict.get('category', '').lower()
        event_keywords = [
            'birthday', 'bday', 'b-day', 'exam', 'test', 'meeting', 'appointment', 'funeral', 
            'wedding', 'anniversary', 'interview', 'presentation', 'conference', 'seminar', 
            'graduation', 'party', 'celebration', 'ceremony', 'event', 'show', 'concert', 
            'game', 'match', 'vacation', 'trip', 'holiday', 'festival', 'outing', 'gathering', 'reunion'
        ]
        event_categories = [
            'event', 'meeting', 'appointment', 'celebration', 'entertainment',
            'travel', 'social', 'ceremony', 'exam', 'interview'
        ]
        is_event = any(keyword in title_lower for keyword in event_keywords) or \
                   any(keyword in category_lower for keyword in event_categories)
        return is_event

    def get_countdown_events(self, user_id: int) -> list:
        """Gets events (not regular tasks) for countdown display. All times in IST."""
        all_tasks = self.db.get_tasks(user_id=user_id, completed=False)
        now_ist = datetime.now(self.ist)
        events = []
        
        for task in all_tasks:
            task_dict = dict(task)
            if task_dict.get('due_time') and self._is_event(task_dict):
                try:
                    due_time_obj = task_dict['due_time']

                    # Ensure timezone awareness in IST
                    if due_time_obj.tzinfo is None:
                        due_time_obj = self.ist.localize(due_time_obj)
                    else:
                        due_time_obj = due_time_obj.astimezone(self.ist)
                    
                    # Handle yearly recurring events
                    if self._is_yearly_recurring_event(task_dict) and due_time_obj < now_ist:
                        next_year = due_time_obj + relativedelta(years=1)
                        task_dict['due_time'] = next_year
                        self.db.update_task_due_time(task_dict['id'], user_id, next_year.isoformat())
                        due_time_obj = next_year
                    
                    task_dict['time_left'] = due_time_obj - now_ist
                    events.append(task_dict)
                    
                except (parser.ParserError, TypeError, ValueError) as e:
                    print(f"⚠️ Error parsing event due_time: {e}")
                    continue
        
        events.sort(key=lambda x: x['time_left'])
        return events

    def mark_task_complete(self, task_id: int, user_id: int):
        """
        Marks a task as complete. If the task is recurring, it resets it for the
        next occurrence instead of marking it permanently complete.
        """
        task = self.db.get_task_by_id(task_id, user_id)
        if not task:
            return "Task not found."
            
        if task['is_recurring'] and task['due_time']:
            current_due_time = task['due_time']
            
            # Ensure timezone awareness
            if current_due_time.tzinfo is None:
                current_due_time = self.ist.localize(current_due_time)
            else:
                current_due_time = current_due_time.astimezone(self.ist)
                
            pattern = task['repeat_pattern'].lower() if task['repeat_pattern'] else ''
            next_due_time = None

            if 'daily' in pattern:
                next_due_time = current_due_time + relativedelta(days=1)
            elif 'weekly' in pattern:
                next_due_time = current_due_time + relativedelta(weeks=1)
            elif 'monthly' in pattern:
                next_due_time = current_due_time + relativedelta(months=1)
            elif 'yearly' in pattern:
                next_due_time = current_due_time + relativedelta(years=1)

            if next_due_time:
                self.db.reset_recurring_task(task_id, user_id, next_due_time.isoformat())
                return f"Task '{task['title']}' completed for today. Next one scheduled for {next_due_time.strftime('%A, %B %d at %I:%M %p IST')}."
        
        self.db.update_task_status(task_id, user_id, is_completed=True)
        return f"Task '{task['title']}' marked as complete."
    
    def delete_task(self, task_id: int, user_id: int):
        """Deletes a task for the specified user."""
        self.db.delete_task(task_id, user_id)
        return f"Task ID {task_id} has been deleted."

    def get_daily_summary(self, user_id: int):
        """Generates a comprehensive daily summary for the user. All times handled in IST."""
        all_tasks = self.db.get_tasks(user_id=user_id, completed=None)
        
        completed_tasks = [dict(t) for t in all_tasks if t['is_completed']]
        pending_tasks = [dict(t) for t in all_tasks if not t['is_completed'] and not self._is_event(dict(t))]
        
        total_tasks = len(completed_tasks) + len(pending_tasks)
        completion_rate = round((len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0)
        
        now_ist = datetime.now(self.ist)
        today = now_ist.date()
        urgent_tasks = []
        overdue_tasks = []
        
        for task in pending_tasks:
            if task.get('due_time'):
                try:
                    due_time_obj = task['due_time']
                    
                    # Ensure timezone awareness
                    if due_time_obj.tzinfo is None:
                        due_time_obj = self.ist.localize(due_time_obj)
                    else:
                        due_time_obj = due_time_obj.astimezone(self.ist)
                    
                    time_diff = due_time_obj - now_ist
                    if time_diff.total_seconds() < 0:
                        overdue_tasks.append(task)
                    elif time_diff.total_seconds() < 86400:  # 24 hours
                        urgent_tasks.append(task)
                        
                except Exception as e:
                    print(f"⚠️ Error processing task time in summary: {e}")
                    pass
        
        summary_data = [
            {'type': 'header', 'content': f"Daily Productivity Report - {today.strftime('%A, %B %d, %Y')} (IST)"},
            {'type': 'metric', 'completed': len(completed_tasks), 'pending': len(pending_tasks), 'completion_rate': completion_rate}
        ]
        
        if overdue_tasks:
            summary_data.extend([
                {'type': 'subheader', 'content': f"🚨 Overdue Tasks ({len(overdue_tasks)})"},
                {'type': 'pending_list', 'tasks': overdue_tasks}
            ])
            
        if urgent_tasks:
            summary_data.extend([
                {'type': 'subheader', 'content': f"⚡ Urgent Tasks (Due within 24 hours)"},
                {'type': 'pending_list', 'tasks': urgent_tasks}
            ])
            
        summary_data.extend([
            {'type': 'subheader', 'content': f"✅ Completed Tasks ({len(completed_tasks)})"},
            {'type': 'completed_list', 'tasks': completed_tasks}
        ])
        
        # Motivational message based on completion rate
        if completion_rate >= 80: 
            motivation_msg = "Outstanding work! You're crushing your goals! 🔥🎯"
        elif completion_rate >= 60: 
            motivation_msg = "Great progress! Keep up the excellent work! 💪✨"
        elif completion_rate >= 40: 
            motivation_msg = "Good effort! You're on the right track. Stay focused! 🚀📈"
        elif completion_rate >= 20: 
            motivation_msg = "Every step counts! Let's tackle those tasks together! 🤝💼"
        else: 
            motivation_msg = "Don't worry, every expert was once a beginner! Let's start small and build momentum! 🌱💪"
        
        summary_data.append({'type': 'motivation', 'content': motivation_msg})
        return summary_data