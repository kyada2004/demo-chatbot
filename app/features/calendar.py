from apscheduler.schedulers.background import BackgroundScheduler
from app.core.utils import show_info

scheduler = BackgroundScheduler()
scheduler.start()

def set_reminder(message, time):
    """Sets a reminder for a specific time."""
    try:
        scheduler.add_job(show_info, 'date', run_date=time, args=["Reminder", message])
        return f"Reminder set for {time}."
    except Exception as e:
        return f"Error setting reminder: {e}"

def show_reminders():
    """Shows all pending reminders."""
    jobs = scheduler.get_jobs()
    if not jobs:
        return "You have no pending reminders."
    
    response = "Your reminders:\n"
    for job in jobs:
        response += f"- {job.name} at {job.next_run_time}\n"
    return response

def delete_reminder(job_id):
    """Deletes a reminder by its ID."""
    try:
        scheduler.remove_job(job_id)
        return "Reminder deleted successfully!"
    except Exception as e:
        return f"Error deleting reminder: {e}"

