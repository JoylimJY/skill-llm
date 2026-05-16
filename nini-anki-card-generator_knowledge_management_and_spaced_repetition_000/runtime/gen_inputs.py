import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# === Deeply nested distractor directory structure ===
dirs = [
    "bootcamp/week3/exercises",
    "bootcamp/week3/solutions",
    "bootcamp/week3/notes",
    "bootcamp/week4/notes",
    "bootcamp/resources/videos",
    "bootcamp/resources/slides",
    "bootcamp/personal/journal",
    "study_tools/notion_exports",
    "study_tools/obsidian_vault/daily",
    "study_tools/obsidian_vault/topics",
    "misc/downloads",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# === Distractor files (realistic bootcamp clutter) ===

(workspace / "bootcamp/week3/exercises/threading_exercise.py").write_text(
    '''import threading

def worker(n):
    print(f"Worker {n} running")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
'''
)

(workspace / "bootcamp/week3/exercises/asyncio_exercise.py").write_text(
    '''import asyncio

async def fetch_data(id):
    await asyncio.sleep(1)
    return f"data_{id}"

async def main():
    results = await asyncio.gather(*[fetch_data(i) for i in range(3)])
    print(results)

asyncio.run(main())
'''
)

(workspace / "bootcamp/week3/solutions/threading_solution.py").write_text(
    '''# Solution: use locks to prevent race conditions
import threading
lock = threading.Lock()
counter = 0

def safe_increment():
    global counter
    with lock:
        counter += 1
'''
)

(workspace / "bootcamp/week3/notes/gil_notes.txt").write_text(
    '''GIL = Global Interpreter Lock
- CPython uses GIL to protect object reference counts
- Only one thread executes Python bytecode at a time
- IO-bound: threads still helpful (GIL released during IO)
- CPU-bound: use multiprocessing instead
- asyncio is single-threaded, uses event loop
- async/await syntax for coroutines
- ThreadPoolExecutor, ProcessPoolExecutor in concurrent.futures
- Race condition: shared state modified by multiple threads without sync
- Deadlock: two threads wait for each other's locks forever
'''
)

(workspace / "bootcamp/week4/notes/concurrency_vs_parallelism.txt").write_text(
    '''Concurrency: dealing with multiple things at once (structure)
Parallelism: doing multiple things at once (execution)
Threading: concurrent but not parallel in CPython (GIL)
Multiprocessing: true parallelism, separate memory spaces
asyncio: cooperative multitasking, single thread
'''
)

(workspace / "bootcamp/resources/slides/week3_concurrency.txt").write_text(
    '''Week 3: Python Concurrency
Slide 1: Motivation - Why concurrency?
Slide 2: Threads vs Processes
Slide 3: The GIL explained
Slide 4: asyncio and event loops
Slide 5: Best practices
'''
)

(workspace / "bootcamp/resources/videos/playlist.txt").write_text(
    "Raymond Hettinger - Thinking About Concurrency\nDavid Beazley - Python Concurrency From the Ground Up\n"
)

(workspace / "bootcamp/personal/journal/2024-01-15.txt").write_text(
    "Struggled with understanding why threading doesn't speed up CPU-bound code. Need to review GIL.\n"
)

(workspace / "study_tools/notion_exports/python_concurrency.md").write_text(
    '''# Python Concurrency Notes (Notion Export)

## Threads
- Thread: lightweight process, shares memory
- `threading.Thread(target=fn)` to create
- `t.start()`, `t.join()`
- Lock: `threading.Lock()`
- RLock: reentrant lock

## asyncio
- Coroutine: defined with `async def`
- Awaitable: coroutines, tasks, futures  
- Event loop: scheduler for coroutines
- `asyncio.run(main())` entry point
- `await asyncio.gather(...)` for concurrent tasks
- `asyncio.Queue` for producer-consumer

## GIL
- Global Interpreter Lock
- Released during IO operations
- Not released for CPU-bound work
- Workaround: multiprocessing module

## concurrent.futures
- ThreadPoolExecutor: thread pool
- ProcessPoolExecutor: process pool
- `executor.submit(fn, *args)` → Future
- `executor.map(fn, iterable)` → results
'''
)

(workspace / "study_tools/obsidian_vault/topics/concurrency.md").write_text(
    '''# Concurrency Patterns

## Producer-Consumer
Use Queue to decouple producers and consumers.

## Reader-Writer
Multiple readers OK, exclusive writer.

## Thread Pool
Reuse threads instead of creating new ones each time.
'''
)

(workspace / "study_tools/obsidian_vault/daily/2024-01-16.md").write_text(
    "- Review asyncio\n- Practice ThreadPoolExecutor\n- Read about GIL internals\n"
)

(workspace / "misc/downloads/python_docs_excerpt.txt").write_text(
    '''From Python docs:
threading.Lock() - A primitive lock is in one of two states, locked or unlocked.
threading.RLock() - A reentrant lock is a synchronization primitive.
asyncio.get_event_loop() - Get the running event loop.
asyncio.create_task() - Schedule the execution of a coroutine.
'''
)

# === The raw "messy" study material the agent must turn into cards ===
# This is intentionally verbose, unstructured, and contains information
# that MUST be split/atomized properly by the agent

(workspace / "bootcamp/week3/concurrency_brain_dump.txt").write_text(
    '''PYTHON CONCURRENCY - BRAIN DUMP FOR ANKI CARDS
================================================
Please turn this into Anki flashcards. I need to memorize these for my interview.

1. GIL (Global Interpreter Lock):
   - It is a mutex that protects access to Python objects, preventing multiple threads 
     from executing Python bytecodes simultaneously in CPython.
   - It is released during IO-bound operations but NOT released for CPU-bound work.
   - The main consequence: threading cannot achieve parallelism for CPU-bound tasks.
   - Workaround for CPU-bound: use the multiprocessing module.

2. Threading vs asyncio:
   - threading: preemptive multitasking, OS decides context switches, shares memory, 
     good for IO-bound tasks, risk of race conditions
   - asyncio: cooperative multitasking, programmer decides yield points (await), 
     single-threaded, no race conditions on shared state, good for many concurrent IO ops

3. concurrent.futures module:
   - ThreadPoolExecutor: manages a pool of worker threads
   - ProcessPoolExecutor: manages a pool of worker processes (bypasses GIL)
   - Both expose: submit(fn, *args) -> Future, map(fn, iterable) -> results iterator
   - Future object: represents eventual result of async computation

4. asyncio key concepts:
   - Coroutine: a function defined with async def, can be suspended with await
   - Event loop: central scheduler, runs coroutines and callbacks
   - Task: wraps a coroutine and schedules it on the event loop (asyncio.create_task)
   - asyncio.gather(): runs multiple awaitables concurrently, returns list of results
   - asyncio.Queue: async-safe queue for producer-consumer patterns

5. Race condition vs Deadlock:
   - Race condition: two or more threads access shared data concurrently and at least 
     one modifies it, outcome depends on scheduling order
   - Deadlock: two or more threads each wait for a resource held by the other, 
     neither can proceed

6. Lock types:
   - Lock (threading.Lock): primitive, can only be acquired once
   - RLock (threading.RLock): reentrant, same thread can acquire multiple times
   - Semaphore: allows N concurrent acquisitions
   - Condition: combines Lock with wait/notify mechanism
'''
)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")