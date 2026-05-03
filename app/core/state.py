stats = {
    "start_time": None,
    "online_visits": 0,
    "projects_found": 0,
    "projects_sent": 0,
    "responses_sent": 0,
    "inbox_checks": 0,
    "new_messages": 0,
    "cookie_refreshes": 0,
    "errors": 0,
}

seen_project_ids: set[str] = set()
prev_inbox_state: dict[str, str] = {}
pending_responses: dict[str, dict] = {}

browser = None
page = None
browser_context = None
monitoring_active = False
auto_respond = True
