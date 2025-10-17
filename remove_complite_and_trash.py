import yougile
from config import Config
import re


def get_feedback_id(tasks_list_yougile):
    feedback_id = []
    count_feedback_id = 0
    for task in tasks_list_yougile:
        description = task.get('description')
        if description and 'feedbackId' in description:
            count_feedback_id += 1
            match = re.search(r"feedbackId:\s*(\d+)", description)
            if match:
                feedback_id.append(match.group(1))
            else:
                print("Не удалось получить feedbackId из задачи: " + description)

    return feedback_id


if __name__ == '__main__':
    completed_tasks = yougile.get_completed_tasks()
    feedback_completed_ids = get_feedback_id(completed_tasks)
    trash_tasks = yougile.get_trash_tasks()
    feedback_trash_ids = get_feedback_id(trash_tasks)

    feedback_ids = feedback_completed_ids + feedback_trash_ids

