You're encountering a series of very common (and frustrating\!) environment setup issues when mixing Windows, WSL, and Python virtual environments. Let's get this absolutely clear and working.

**Crucial Point: All your Python development (Django, Celery, virtual environments, `pip` commands) and service running (Redis, Celery worker) for this project should happen *inside your WSL terminal*.**

Even though your project files are on your `I:` drive in Windows, WSL can access them via `/mnt/i/Online_Judge`. This is where you need to do all your work for this Django project's backend.

Let's go through a **complete, step-by-step reset of your environment setup within WSL** to eliminate these conflicts. Follow these steps meticulously in your WSL terminal.

-----

### **Definitive Guide: Setting Up Your Development Environment in WSL**

**Step 0: Start Fresh & Clean Up**

1.  **Close ALL WSL terminal windows.** This is vital to clear any previous environment states.
2.  **Open a brand new WSL terminal.** Your prompt should likely be `sriram@SRIRAM:~$` or `(base) sriram@SRIRAM:~$` if you have Anaconda/Miniconda.
3.  **Navigate to your Django project directory in WSL:**
    ```bash
    cd /mnt/i/Online_Judge
    ```
4.  **Delete any existing virtual environment folder** (e.g., `venv` or `.venv`) to ensure a completely clean start:
    ```bash
    rm -rf venv .venv # This command will remove both if they exist
    ```

-----

**Step 1: Install Necessary System Packages in WSL**

First, ensure your WSL has the tools required for Python virtual environments and Redis.

1.  **Update package list:**
    ```bash
    sudo apt update
    ```
2.  **Install `python3-venv`:** This package provides the `venv` module for creating virtual environments. The error `ensurepip is not available` means this was missing.
    ```bash
    sudo apt install python3.12-venv # Use python3.12-venv as your error suggested
    # If python3.12-venv is not found, try `sudo apt install python3-venv`
    ```
3.  **Install `redis-server`:** This installs the Redis database server. You confirmed this was missing.
    ```bash
    sudo apt install redis-server
    ```
4.  **Add your user to the `docker` group in WSL:** This allows your user to run Docker commands without `sudo`.
    ```bash
    sudo groupadd docker   # Create the group if it doesn't exist
    sudo usermod -aG docker $USER # Add your user to the group
    ```
      * **After this `usermod` command, you MUST close and reopen your WSL terminal** for the group change to take effect. Do this now before proceeding to Step 2.

-----

**Step 2: Create and Activate Your Project's Virtual Environment**

1.  **Open a NEW WSL terminal.** (After closing and reopening from Step 1).

2.  **Navigate to your project directory:**

    ```bash
    cd /mnt/i/Online_Judge
    ```

3.  **Create the virtual environment:**

    ```bash
    python3 -m venv venv
    ```

    This creates a folder named `venv` inside your `Online_Judge` directory.

4.  **Activate your virtual environment:**

    ```bash
    source venv/bin/activate
    ```

    **VERIFY YOUR PROMPT:** Your terminal prompt **must** now start with `(venv)`, like `(venv) sriram@SRIRAM:/mnt/i/Online_Judge$`. If it doesn't, the virtual environment is NOT active. Stop and troubleshoot this step.

-----

**Step 3: Install Project-Specific Python Packages**

Now that your `(venv)` is active, we'll install Django, Celery, and Redis *into this isolated environment*. This avoids the "externally-managed-environment" error.

1.  **Install Django, Celery, and Redis:**

    ```bash
    python -m pip install Django celery redis
    ```

      * **Why `python -m pip`?** This explicitly tells the `python` executable (which is the one inside your active `venv`) to use *its* `pip` module, ensuring packages go into the virtual environment and bypass system restrictions.
      * Let this command complete. It might take a moment.

2.  **Verify installations (optional, but good for debugging):**

    ```bash
    pip freeze
    ```

    You should see `Django`, `celery`, `redis`, and their dependencies (like `vine`) listed. All these packages are now isolated within your `venv`.

-----

**Step 4: Run Your Services (Each in a Separate WSL Terminal)**

Now you're ready to run all components correctly. You will need three separate WSL terminal windows open.

1.  **Terminal 1: Start Django Development Server**

      * Open a new WSL terminal.
      * `cd /mnt/i/Online_Judge`
      * `source venv/bin/activate`
      * `python manage.py runserver`

2.  **Terminal 2: Start Redis Server**

      * Open another new WSL terminal without any virtual environment or conda env.
      * ```bash
          sudo systemctl start redis-server
        ```
        *If this *still* fails with "Failed to start redis-server.service: Unit redis-server.service not found." (after you installed it with `apt`), then your WSL might not use `systemd`. In that case, run this instead:*
        ```bash
        redis-server
        ```
        *(This terminal will be occupied by Redis).*

3.  **Terminal 3: Start Celery Worker**

      * Open a third new WSL terminal.
      * `cd /mnt/i/Online_Judge`
      * `source venv/bin/activate`
      * **Crucially, use `python -m celery` here:**
        ```bash
        python -m celery -A Online_Judge worker -l info
        ```

This should finally get all your components running correctly without the errors you've been seeing. Take your time with each step, and ensure the virtual environment is always active when installing Python packages or running Django/Celery commands.