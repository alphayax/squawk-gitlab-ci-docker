import os
import json
import requests
from collections import defaultdict
from hashlib import sha256

# Configuration-
GITLAB_API_URL = f"{os.getenv('CI_API_V4_URL', '/api/v4')}"
NOTE_TAG = "<!-- DB-REPORT-AUTO -->"

def make_entry_key(entry):
    data = {
        "file": entry["file"],
        "line": entry["line"],
        "column": entry["column"],
        "level": entry["level"],
        "rule_name": entry["rule_name"],
        "messages": entry["messages"]
    }
    return sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def group_by_file(json_data):
    grouped = defaultdict(list)
    seen_entries = set()

    for item in json_data:
        entry_key = make_entry_key(item)
        if entry_key in seen_entries:
            continue
        seen_entries.add(entry_key)
        grouped[item["file"]].append(item)

    return grouped

def json_to_markdown(json_data):
    grouped_data = group_by_file(json_data)
    markdown_lines = [NOTE_TAG]  # identifier tag

    for file, entries in grouped_data.items():
        markdown_lines.append(f"## `{file}`")

        for item in sorted(entries, key=lambda x: x["line"]):
            line = item.get("line", "Unknown line")
            level = item.get("level", "Info")
            rule = item.get("rule_name", "Unknown rule")

            level_emoji = {
                "warning": "🔶",
                "error": "🟥",
                "info": "ℹ️"
            }.get(level.lower(), "❔")

            markdown_lines.append(f"### line {line}: {level_emoji} **{level}** – _{rule}_")

            for message in item.get("messages", []):
                for key, value in message.items():
                    prefix = {
                        "note": "💬",
                        "help": "💡"
                    }.get(key.lower(), "✏️")
                    markdown_lines.append(f"- {prefix} **{key}**: {value}")

            markdown_lines.append("")

    return "\n".join(markdown_lines)

def get_existing_note_id(project_id, merge_request_iid, token):
    url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{merge_request_iid}/notes"
    headers = {"PRIVATE-TOKEN": token}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch notes: {response.status_code}")
        return None

    notes = response.json()
    for note in notes:
        if NOTE_TAG in note.get("body", ""):
            return note["id"]
    return None

def create_or_update_note(project_id, merge_request_iid, markdown, token):
    note_id = get_existing_note_id(project_id, merge_request_iid, token)
    headers = {"PRIVATE-TOKEN": token}

    if note_id:
        print(f"🔁 Updating existing note (id: {note_id})...")
        url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{merge_request_iid}/notes/{note_id}"
        response = requests.put(url, headers=headers, data={"body": markdown})
    else:
        print("🆕 Creating new note...")
        url = f"{GITLAB_API_URL}/projects/{project_id}/merge_requests/{merge_request_iid}/notes"
        response = requests.post(url, headers=headers, data={"body": markdown})

    if response.status_code in [200, 201]:
        print("✅ Note successfully posted/updated on the merge request.")
    else:
        print(f"❌ Failed to post/update note: {response.status_code}")
        print(response.text)

# Main execution
if __name__ == "__main__":
    input_file = "db-report.json"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    markdown_output = json_to_markdown(data)

    print("📝 Generated Markdown:\n")
    print(markdown_output)

    project_id = os.getenv("CI_MERGE_REQUEST_PROJECT_ID")
    merge_request_iid = os.getenv("CI_MERGE_REQUEST_IID")
    token = os.getenv("COMMENT_GITLAB_TOKEN")

    if project_id and merge_request_iid and token:
        print(f"\n🚀 Syncing note with Merge Request {merge_request_iid} in project {project_id}...")
        create_or_update_note(project_id, merge_request_iid, markdown_output, token)
    else:
        print("\n⚠️ Missing environment variables: CI_MERGE_REQUEST_PROJECT_ID, CI_MERGE_REQUEST_IID, or COMMENT_GITLAB_TOKEN.")
