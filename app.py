import os
import sys
import subprocess
import streamlit as st

# Ensure root directory is added to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import init_db
from database.seed import seed_database
from ui.interface import run_interface


def main():
    """
    Main execution function.
    If executed by Streamlit (`streamlit run app.py`), `st.runtime.exists()` is true and renders the interface.
    If executed via standard Python (`python app.py`), checks/seeds the database and launches Streamlit automatically.
    """
    try:
        if st.runtime.exists():
            # Running inside Streamlit server
            init_db()
            run_interface()
        else:
            # Executed via `python app.py` directly from terminal
            print("=================================================")
            print("  Starting Student Service Chatbot Application   ")
            print("=================================================")
            print("Verifying database and sample data seeding...")
            seed_database()
            print("Database check complete!")
            print("Launching Streamlit interface automatically...")
            
            # Run `streamlit run app.py` using subprocess
            cmd = [sys.executable, "-m", "streamlit", "run", __file__]
            subprocess.run(cmd, check=True)
            
    except AttributeError:
        # Fallback for older Streamlit versions without st.runtime.exists()
        init_db()
        run_interface()
    except KeyboardInterrupt:
        print("\nApplication stopped cleanly by user.")
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()
