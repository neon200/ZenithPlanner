# ZenithPlanner/llm_utils.py

import google.generativeai as genai
import json
from datetime import datetime, timedelta
import pytz
import re
from config import GEMINI_API_KEY

# Configure the Gemini API client
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini AI model loaded successfully.")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
    model = None

def parse_time_manually(user_input: str, current_time_ist: datetime) -> str:
    """
    Manual time parsing as a fallback/validation for Gemini's output.
    Handles common Indian time expressions more accurately.
    """
    user_input_lower = user_input.lower()
    
    # Handle relative times first
    if 'in ' in user_input_lower:
        # Extract "in X hours/minutes"
        hours_match = re.search(r'in (\d+) hours?', user_input_lower)
        minutes_match = re.search(r'in (\d+) minutes?', user_input_lower)
        
        if hours_match:
            hours = int(hours_match.group(1))
            return (current_time_ist + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
        elif minutes_match:
            minutes = int(minutes_match.group(1))
            return (current_time_ist + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")
    
    # Handle specific times
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 9:30 PM
        r'(\d{1,2})\s*(am|pm)',          # 9 PM
        r'(\d{1,2}):(\d{2})',            # 21:30 (24-hour)
        r'(\d{1,2})\s*o\'?clock',        # 9 o'clock
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, user_input_lower)
        if match:
            if len(match.groups()) >= 3:  # Has AM/PM
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                am_pm = match.group(3)
                
                # Convert to 24-hour format
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
            elif len(match.groups()) == 2 and match.group(2) in ['am', 'pm']:  # X AM/PM
                hour = int(match.group(1))
                minute = 0
                am_pm = match.group(2)
                
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
            else:  # 24-hour format or o'clock
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
                
                # Smart inference for ambiguous times
                if hour <= 12:
                    # Check context for evening/dinner/night keywords
                    evening_keywords = ['dinner', 'evening', 'night', 'pm', 'tonight']
                    if any(keyword in user_input_lower for keyword in evening_keywords):
                        if hour < 12:  # Don't add 12 to 12 o'clock
                            hour += 12
            
            # Determine the date
            target_date = current_time_ist.date()
            target_time = current_time_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the time has passed today, schedule for tomorrow
            if target_time <= current_time_ist:
                target_date = (current_time_ist + timedelta(days=1)).date()
                target_time = target_time.replace(year=target_date.year, month=target_date.month, day=target_date.day)
            
            return target_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    return None

def parse_task_with_gemini(user_input: str) -> dict:
    if not model:
        return {"error": "Gemini model is not available."}

    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    current_time_str = current_time_ist.strftime("%Y-%m-%d %A, %I:%M %p IST")
    
    # Calculate some reference times for better context
    one_hour_later = (current_time_ist + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    tomorrow_9am = (current_time_ist + timedelta(days=1)).replace(hour=9, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
    end_of_month = current_time_ist.replace(day=28) + timedelta(days=4)
    end_of_month = end_of_month - timedelta(days=end_of_month.day)
    end_of_month = end_of_month.replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S")
    
    # Try manual parsing first for common patterns
    manual_time = parse_time_manually(user_input, current_time_ist)

    prompt = f"""
    You are an expert task parsing system for ZenithPlanner. Your job is to analyze user text and convert it into structured JSON format.

    **CRITICAL TIMEZONE CONTEXT:**
    - Current IST time: {current_time_str}
    - User is in India (IST timezone)
    - ALL times should be interpreted in IST context
    - When user says relative times like "in 1 hour", "tomorrow", calculate from current IST time

    **User's Task Description:** "{user_input}"

    **CRITICAL TIME PARSING RULES:**
    - "9 PM" or "9pm" = 21:00 (NOT 09:00 or 01:00)
    - "9 AM" or "9am" = 09:00 (NOT 21:00)
    - "dinner" context + time = evening time (6 PM - 11 PM range)
    - "lunch" context + time = afternoon time (12 PM - 3 PM range)
    - "breakfast" context + time = morning time (6 AM - 11 AM range)
    - If no AM/PM specified but context suggests evening (dinner, night, etc.) = PM time
    - "in 1 hour" from now ({current_time_str}) = {one_hour_later}
    - "tomorrow morning" = {tomorrow_9am} (9 AM next day)
    - "end of month" = {end_of_month}

    **CRITICAL RECURRING EVENT DETECTION:**
    **These are ALWAYS recurring events (set is_recurring=true, repeat_pattern="yearly"):**
    - Birthdays, B-days, Birth anniversaries
    - Wedding anniversaries, Marriage anniversaries  
    - Death anniversaries, Memorial days
    - Graduation days, Graduation anniversaries
    - Work anniversaries, Job anniversaries
    - Any event with "anniversary" in the name
    - National holidays, Religious festivals that repeat yearly

    **These are ALWAYS recurring events (set is_recurring=true with appropriate pattern):**
    - Daily: "every day", "daily", "each day"
    - Weekly: "every week", "weekly", "each week", "every Monday/Tuesday/etc"
    - Monthly: "every month", "monthly", "each month", "1st of every month"
    - Yearly: "every year", "annually", "each year"

    **Examples of RECURRING vs NON-RECURRING:**
    - "Dad's birthday Nov 11" → is_recurring=true, repeat_pattern="yearly" 
    - "Mom's birthday" → is_recurring=true, repeat_pattern="yearly"
    - "Wedding anniversary" → is_recurring=true, repeat_pattern="yearly"
    - "Submit report by Friday" → is_recurring=false
    - "Call doctor" → is_recurring=false
    - "Take medicine daily" → is_recurring=true, repeat_pattern="daily"

    **EXAMPLES OF CORRECT TIME INTERPRETATION:**
    - "dinner at 9pm" → 21:00 (9 PM)
    - "dinner at 9" → 21:00 (9 PM, inferred from dinner context)
    - "meeting at 9am" → 09:00 (9 AM)
    - "lunch at 1" → 13:00 (1 PM, inferred from lunch context)
    - "breakfast at 8" → 08:00 (8 AM, inferred from breakfast context)

    **Your Task:**
    Analyze the user's description and extract details. Respond ONLY with a single, minified JSON object.

    **JSON Schema:**
    - `title` (string): A concise title for the task.
    - `due_time` (string | null): The deadline in strict ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If no specific time or date is found, this MUST be `null`. **CRITICAL**: Pay attention to meal/activity context - dinner=evening, lunch=afternoon, breakfast=morning.
    - `category` (string): Generate a concise category that best fits the task (e.g., "Work", "Health", "Personal", "Finance", "Meeting").
    - `is_recurring` (boolean): `true` if the task repeats (birthdays, anniversaries, daily/weekly/monthly tasks), otherwise `false`.
    - `repeat_pattern` (string | null): Pattern like "daily", "weekly", "monthly", "yearly". MUST be "yearly" for birthdays/anniversaries. `null` if not recurring.
    - `user_notes` (string | null): Any extra details from the user. `null` if none.

    **Examples with Current Context:**
    1. Input: "Dad's birthday Nov 11"
       Output: {{"title":"Dad's Birthday","due_time":"2025-11-11T18:30:00","category":"Personal","is_recurring":true,"repeat_pattern":"yearly","user_notes":null}}
    
    2. Input: "Mom's birthday"
       Output: {{"title":"Mom's Birthday","due_time":null,"category":"Personal","is_recurring":true,"repeat_pattern":"yearly","user_notes":"Date not specified"}}

    3. Input: "Wedding anniversary March 15"
       Output: {{"title":"Wedding Anniversary","due_time":"2026-03-15T18:30:00","category":"Personal","is_recurring":true,"repeat_pattern":"yearly","user_notes":null}}

    4. Input: "dinner at 9pm"
       Output: {{"title":"Dinner","due_time":"2025-06-11T21:00:00","category":"Personal","is_recurring":false,"repeat_pattern":null,"user_notes":null}}
    
    5. Input: "take medicine daily at 8am"
       Output: {{"title":"Take Medicine","due_time":"2025-06-12T08:00:00","category":"Health","is_recurring":true,"repeat_pattern":"daily","user_notes":null}}

    6. Input: "submit report by Friday"
       Output: {{"title":"Submit Report","due_time":"2025-06-13T17:00:00","category":"Work","is_recurring":false,"repeat_pattern":null,"user_notes":null}}

    **REMEMBER:** Birthdays and anniversaries are ALWAYS yearly recurring events. This is basic common sense.

    Now, process the user's task description.
    """

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        task_data = json.loads(cleaned_response)
        
        # Validation and correction using manual parsing
        if task_data.get('due_time') and manual_time:
            # If manual parsing found a time, compare with Gemini's result
            try:
                gemini_time = datetime.fromisoformat(task_data['due_time'])
                manual_time_obj = datetime.fromisoformat(manual_time)
                
                # If there's a significant difference (more than 12 hours), prefer manual parsing
                time_diff = abs((gemini_time - manual_time_obj).total_seconds())
                if time_diff > 43200:  # 12 hours in seconds
                    print(f"⚠️ Time correction: Gemini suggested {task_data['due_time']}, manual parsing suggests {manual_time}")
                    task_data['due_time'] = manual_time
                    if not task_data.get('user_notes'):
                        task_data['user_notes'] = "Time automatically corrected for IST context"
                        
            except Exception as e:
                print(f"⚠️ Time validation error: {e}")
        
        # Additional validation for past times
        if task_data.get('due_time'):
            try:
                parsed_time = datetime.fromisoformat(task_data['due_time'])
                # If time is in the past and it's not a relative time, assume it's for tomorrow
                if parsed_time < current_time_ist and not any(phrase in user_input.lower() for phrase in ['in ', 'after ', 'ago']):
                    # Move to tomorrow
                    tomorrow_time = parsed_time + timedelta(days=1)
                    task_data['due_time'] = tomorrow_time.strftime("%Y-%m-%dT%H:%M:%S")
                    print(f"⚠️ Time moved to tomorrow: {task_data['due_time']}")
                        
            except Exception as e:
                print(f"⚠️ Time validation error: {e}")
        
        return task_data
        
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return {"error": "An error occurred while processing your request with the AI."}