import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# 1. Open the existing database
conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# 2. Get all distinct thread IDs stored in the database
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
thread_ids = [row[0] for row in cursor.fetchall()]

print(f"Found {len(thread_ids)} thread(s) in checkpoints.db:\n")

# 3. Iterate through each thread and inspect checkpoints
for thread_id in thread_ids:
    print(f"{'='*60}")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*60}")

    config = {"configurable": {"thread_id": thread_id}}
    
    # list() yields CheckpointTuple objects ordered newest to oldest
    checkpoints = list(checkpointer.list(config)) # type: ignore
    print(f"Total snapshots for this thread: {len(checkpoints)}\n")

    for i, cp_tuple in enumerate(reversed(checkpoints), start=1):
        step_metadata = cp_tuple.metadata  # Contains node name, step number, etc.
        state_values = cp_tuple.checkpoint.get("channel_values", {})

        source_node = step_metadata.get("source", "start")
        step_num = step_metadata.get("step", i)

        print(f"  [Step {step_num}] Node: {source_node}")
        print(f"  Checkpoint ID: {cp_tuple.checkpoint['id']}")
        
        # Keys stored in state at this point in time
        print(f"  State keys present: {list(state_values.keys())}")

        # Example: inspect specific keys if they exist in state
        if "plan" in state_values:
            print(f"    - Planned topics count: {len(state_values['plan'])}")
        if "current_topic_index" in state_values:
            print(f"    - Current Topic Index: {state_values['current_topic_index']}")
        if "raw_findings" in state_values:
            print(f"    - Researched topics: {list(state_values['raw_findings'].keys())}")
        if "messages" in state_values:
            print(f"    - Total messages in state: {len(state_values['messages'])}")

        print("-" * 50)

conn.close()