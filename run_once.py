import sys
from main import job

if __name__ == "__main__":
    print("Executing one-off automated post job...")
    try:
        job()
        print("Job finished successfully.")
    except Exception as e:
        print(f"Job failed with exception: {e}")
        sys.exit(1)
