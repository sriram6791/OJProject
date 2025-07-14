# judge_core/judge.py

import subprocess
import os
import tempfile
import shutil
import time
import sys
import sys # Import sys for fallback function

# Remove module-level model imports to avoid circular imports

# --- REMOVE THESE LINES ---
# TEMP_DIR_BASE = os.path.join(tempfile.gettempdir(), "oj_submissions")
# os.makedirs(TEMP_DIR_BASE, exist_ok=True)
# --- END REMOVAL ---

def _run_docker_command(command, time_limit, memory_limit_mb, stdin_data=None, work_dir="/tmp"):
    """
    Executes a shell command inside a Docker container.
    Handles time and memory limits.
    Returns (stdout, stderr, exit_code, status_message).
    """
    container_name = f"oj_run_{os.urandom(8).hex()}" # Unique name for container

    # Docker run command template
    # --rm: Automatically remove the container when it exits
    # --network=none: Disable network access for security
    # --memory=<limit>m: Set memory limit
    # --name: Assign a unique name to the container
    # -i: Keep stdin open
    # -a stdin,stdout,stderr: Attach to stdin, stdout, and stderr
    # -w: Set working directory inside the container
    docker_cmd_prefix = [
        "docker", "run", "--rm", "--network=none",
        f"--memory={memory_limit_mb}m",
        f"--name={container_name}",
        "-i", # Keep stdin open
        "-a", "stdin", "-a", "stdout", "-a", "stderr",
        "-w", work_dir # Set working directory inside container
    ]

    try:
        # Using subprocess.Popen for more control over stdin and timeout
        # preexec_fn=os.setsid is used to create a new session ID for the child process,
        # which allows us to kill the entire process group if a timeout occurs.
        process = subprocess.Popen(
            docker_cmd_prefix + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Decode stdout/stderr as text
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        stdout_data, stderr_data = None, None
        status_message = "Success"
        start_time = time.time()

        try:
            # Communicate with a timeout
            stdout_data, stderr_data = process.communicate(input=stdin_data, timeout=time_limit)
        except subprocess.TimeoutExpired:
            # Kill the process group to ensure the Docker container is stopped
            os.killpg(process.pid, 9) # Send SIGKILL to the process group
            process.wait() # Wait for the process to actually terminate
            stdout_data, stderr_data = process.communicate() # Collect any remaining output
            status_message = "Time Limit Exceeded"
            return stdout_data, stderr_data, 124, status_message # 124 is commonly used for timeout

        end_time = time.time()
        elapsed_time = end_time - start_time # This is just simple elapsed time, not resource usage

        # Check for OOM (Out Of Memory) from Docker
        # Docker's exit code for OOM is often 137, but it can vary.
        # Alternatively, check stderr for "Out of memory" or similar phrases from Docker daemon.
        if process.returncode == 137 or "Out of memory" in stderr_data: # Basic check for OOM
             status_message = "Memory Limit Exceeded"
             return stdout_data, stderr_data, 137, status_message # Return appropriate exit code

        # Check for other errors
        if process.returncode != 0 and status_message == "Success":
            status_message = "Runtime Error" # Generic runtime error if non-zero exit code

        return stdout_data, stderr_data, process.returncode, status_message

    except FileNotFoundError:
        return "", "Docker command not found. Is Docker installed and in PATH?", 1, "System Error"
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode, "System Error"
    except Exception as e:
        return "", str(e), 1, "Unexpected System Error"


def judge_python(code, input_data, time_limit, memory_limit_mb):
    """
    Judges Python code using a Docker container.
    Returns (output, error, verdict, execution_time, memory_used).
    """
    # Create temp directory with proper permissions
    with tempfile.TemporaryDirectory() as temp_dir:
        # Ensure temp_dir has proper permissions
        os.chmod(temp_dir, 0o755)
        
        code_file_path = os.path.join(temp_dir, "solution.py")
        with open(code_file_path, "w") as f:
            f.write(code)
        
        # Make sure the file is readable
        os.chmod(code_file_path, 0o644)

        # Docker command to run Python script
        # -v: Mount the temporary directory into the container
        # python:3.9-slim is a lightweight Python image
        command = ["python", "/tmp/solution.py"]
        docker_command = ["-v", f"{temp_dir}:/tmp", "python:3.9-slim"] + command

        stdout, stderr, exit_code, status_message = _run_docker_command(
            docker_command, time_limit, memory_limit_mb, stdin_data=input_data, work_dir="/tmp" # Passed work_dir
        )

        execution_time = 0.0 # Placeholder, will be more accurate with cgroup/stats
        memory_used = 0.0 # Placeholder

        verdict = "pending" # Default if not determined

        if status_message == "Time Limit Exceeded":
            verdict = "time_limit_exceeded"
        elif status_message == "Memory Limit Exceeded":
            verdict = "memory_limit_exceeded"
        elif exit_code != 0:
            verdict = "runtime_error" # Or specific compilation_error if applicable (not for python directly)
        else:
            verdict = "success" # Program ran successfully, now compare output

        return stdout, stderr, verdict, execution_time, memory_used


def judge_cpp(code, input_data, time_limit, memory_limit_mb):
    """
    Judges C++ code using a Docker container. Involves compilation and then execution.
    Returns (output, error, verdict, execution_time, memory_used).
    """
    # --- MODIFIED LINE: Removed dir=TEMP_DIR_BASE ---
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file_path = os.path.join(temp_dir, "solution.cpp")
        # executable_file_path = os.path.join(temp_dir, "solution") # Not strictly needed

        with open(source_file_path, "w") as f:
            f.write(code)

        # --- Compilation Step ---
        # Mount the temp_dir to /tmp in the container
        # Run g++ /tmp/solution.cpp -o /tmp/solution inside the container
        compile_command = ["g++", "solution.cpp", "-o", "solution"] # Refer to filename, not path
        docker_compile_command = ["-v", f"{temp_dir}:/tmp", "gcc:latest"] + compile_command

        compile_stdout, compile_stderr, compile_exit_code, compile_status_message = _run_docker_command(
            docker_compile_command,
            time_limit=10,
            memory_limit_mb=memory_limit_mb,
            work_dir="/tmp" # Crucially, set the working directory for g++
        )

        if compile_exit_code != 0:
            return "", compile_stderr, "compilation_error", 0.0, 0.0

        # --- Execution Step ---
        # Run /tmp/solution inside the container
        execute_command = ["./solution"] # Execute relative to work_dir
        docker_execute_command = ["-v", f"{temp_dir}:/tmp", "gcc:latest"] + execute_command

        stdout, stderr, execute_exit_code, execute_status_message = _run_docker_command(
            docker_execute_command,
            time_limit,
            memory_limit_mb,
            stdin_data=input_data,
            work_dir="/tmp" # Crucially, set the working directory for execution
        )

        execution_time = 0.0 # Placeholder
        memory_used = 0.0 # Placeholder

        verdict = "pending" # Default

        if execute_status_message == "Time Limit Exceeded":
            verdict = "time_limit_exceeded"
        elif execute_status_message == "Memory Limit Exceeded":
            verdict = "memory_limit_exceeded"
        elif execute_exit_code != 0:
            verdict = "runtime_error"
        else:
            verdict = "success" # Program ran successfully

        return stdout, stderr, verdict, execution_time, memory_used

def judge_java(code, input_data, time_limit, memory_limit_mb):
    """
    Judges Java code using a Docker container. Involves compilation and then execution.
    Assumes the main class is named 'Solution'.
    """
    # --- MODIFIED LINE: Removed dir=TEMP_DIR_BASE ---
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file_name = "Solution.java" # Define the source file name
        source_file_path_host = os.path.join(temp_dir, source_file_name) # Host path

        with open(source_file_path_host, "w") as f:
            f.write(code)

        # --- Compilation Step ---
        # Using openjdk:11-slim image for Java
        # Mount the temp_dir to /tmp in the container
        # Run javac Solution.java inside the container from /tmp
        compile_command = ["javac", source_file_name] # Just the filename, work_dir is /tmp
        docker_compile_command = ["-v", f"{temp_dir}:/tmp", "openjdk:11-slim"] + compile_command

        compile_stdout, compile_stderr, compile_exit_code, compile_status_message = _run_docker_command(
            docker_compile_command,
            time_limit=10, # Compilation usually has a generous time limit
            memory_limit_mb=memory_limit_mb,
            work_dir="/tmp" # Crucially, set the working directory for javac
        )

        if compile_exit_code != 0:
            return "", compile_stderr, "compilation_error", 0.0, 0.0

        # --- Execution Step ---
        # Run java Solution inside the container (from /tmp directory where .class file is)
        # The .class file is also in /tmp because javac compiled it there.
        # We need to ensure 'java Solution' is run from /tmp.
        execute_command = ["java", "Solution"] # Just the class name, not .class
        docker_execute_command = ["-v", f"{temp_dir}:/tmp", "openjdk:11-slim"] + execute_command

        stdout, stderr, execute_exit_code, execute_status_message = _run_docker_command(
            docker_execute_command,
            time_limit,
            memory_limit_mb,
            stdin_data=input_data,
            work_dir="/tmp" # Crucially, set the working directory for java
        )

        verdict = "pending"
        execution_time = 0.0
        memory_used = 0.0

        if execute_status_message == "Time Limit Exceeded":
            verdict = "time_limit_exceeded"
        elif execute_status_message == "Memory Limit Exceeded":
            verdict = "memory_limit_exceeded"
        elif execute_exit_code != 0:
            verdict = "runtime_error"
        else:
            verdict = "success"

        return stdout, stderr, verdict, execution_time, memory_used


def clean_output(output_str):
    """Cleans up extra whitespace and newlines for consistent comparison."""
    if not output_str:
        return ""
    return '\n'.join([line.strip() for line in output_str.strip().splitlines()]).strip()


def evaluate_solution(submission_id):
    """
    Main function called by Celery task to evaluate a submission.
    This will update the Submission object in the database.
    """
    # Import inside function to avoid circular import issues with Celery
    from submissions.models import Submission
    from problems.models import Problem, TestCase

    try:
        submission = Submission.objects.get(id=submission_id)
        problem = submission.problem
        test_cases = problem.test_cases.all().order_by('order')

        submission.status = 'processing'
        submission.save(update_fields=['status'])

        passed_count = 0
        total_count = test_cases.count()

        # Define limits (should align with problem difficulty or problem specific settings)
        TIME_LIMIT_SECONDS = 5
        MEMORY_LIMIT_MB = 256

        final_verdict = "accepted"
        last_error_message = "" # To store the most relevant error message

        for i, test_case in enumerate(test_cases):
            input_data = test_case.input_data
            expected_output = test_case.expected_output

            stdout = ""
            stderr = ""
            verdict_for_test_case = "pending"
            execution_time_tc = 0.0
            memory_used_tc = 0.0

            if submission.language == 'python':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_python_fallback(
                    submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            elif submission.language == 'cpp':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_cpp(
                    submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            elif submission.language == 'java':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_java(
                    submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            else:
                verdict_for_test_case = "runtime_error" # Unsupported language
                stderr = "Unsupported language for judging."

            # Update final_verdict based on test case result
            if verdict_for_test_case == "success":
                if clean_output(stdout) == clean_output(expected_output):
                    passed_count += 1
                else:
                    verdict_for_test_case = "wrong_answer"
                    # If it's a WA, the overall verdict becomes WA unless a more severe error occurs
                    if final_verdict == "accepted":
                        final_verdict = "wrong_answer"
            else:
                # If a test case fails, its verdict might become the overall verdict
                # Prioritize errors: CE > RE > TLE/MLE > WA
                if verdict_for_test_case == "compilation_error":
                    final_verdict = "compilation_error"
                    last_error_message = stderr
                    break # Stop evaluating further test cases for CE
                elif verdict_for_test_case == "runtime_error":
                    # Only upgrade to RE if current is AC/WA/TLE/MLE
                    if final_verdict in ["accepted", "wrong_answer", "time_limit_exceeded", "memory_limit_exceeded"]:
                        final_verdict = "runtime_error"
                        last_error_message = stderr
                    break # Stop evaluating further test cases for RE
                elif verdict_for_test_case == "time_limit_exceeded":
                    # Only upgrade if current is AC/WA
                    if final_verdict in ["accepted", "wrong_answer"]:
                        final_verdict = "time_limit_exceeded"
                        last_error_message = stderr
                elif verdict_for_test_case == "memory_limit_exceeded":
                    # Only upgrade if current is AC/WA
                    if final_verdict in ["accepted", "wrong_answer"]:
                        final_verdict = "memory_limit_exceeded"
                        last_error_message = stderr
                elif verdict_for_test_case == "wrong_answer":
                    # This case should technically be caught by "verdict_for_test_case == 'success'" logic
                    # but including for robustness.
                    if final_verdict == "accepted":
                        final_verdict = "wrong_answer"

            # For simplicity, we'll store the execution time/memory of the last test case,
            # or you might want to store the maximum across all tests.
            # For this basic setup, this is fine.
            submission.execution_time = execution_time_tc
            submission.memory_used = memory_used_tc

        submission.status = 'finished'
        submission.passed_test_cases = passed_count
        submission.total_test_cases = total_count
        submission.final_verdict = final_verdict
        submission.error_message = last_error_message

        submission.save()
        print(f"Submission {submission.id} for Problem {problem.name} finished with verdict: {final_verdict}")

    except Exception as e:
        # Import inside exception handler to avoid circular import issues
        from submissions.models import Submission
        print(f"Submission with ID {submission_id} does not exist.")
        print(f"Error evaluating submission {submission_id}: {e}")
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.status = 'finished'
            submission.final_verdict = 'runtime_error'
            submission.error_message = f"Judge system error: {e}"
            submission.save()
        except:
            pass
        
def evaluate_contest_solution(contest_submission_id):
    """
    Main function called by Celery task to evaluate a CONTEST Submission.
    This will update the ContestSubmission object in the database.
    """
    # Import inside function to avoid circular import issues
    from contests.models import ContestSubmission, ContestProblem
    from problems.models import Problem, TestCase

    try:
        contest_submission = ContestSubmission.objects.get(id=contest_submission_id)
        contest_problem = contest_submission.contest_problem
        problem = contest_problem.problem
        test_cases = problem.test_cases.all().order_by('order')

        # Calculate total count first
        total_count = test_cases.count()

        # Initialize submission state properly
        contest_submission.status = 'processing'  # Only use: pending, processing, finished
        contest_submission.final_verdict = 'pending'  # Explicitly set to pending initially
        contest_submission.execution_time = 0.0
        contest_submission.memory_used = 0.0
        contest_submission.test_cases_passed = 0
        contest_submission.total_test_cases = total_count
        contest_submission.score = 0
        contest_submission.save(force_update=True)  # Force update to ensure all fields are saved

        passed_count = 0

        # Define limits
        TIME_LIMIT_SECONDS = getattr(problem, 'time_limit', 5)
        MEMORY_LIMIT_MB = getattr(problem, 'memory_limit', 256)
        
        if not TIME_LIMIT_SECONDS: TIME_LIMIT_SECONDS = 5
        if not MEMORY_LIMIT_MB: MEMORY_LIMIT_MB = 256

        final_verdict = "accepted"  # Start optimistic
        last_error_message = ""

        for i, test_case in enumerate(test_cases):
            input_data = test_case.input_data
            expected_output = test_case.expected_output

            stdout = ""
            stderr = ""
            verdict_for_test_case = "pending"
            execution_time_tc = 0.0
            memory_used_tc = 0.0

            # Run the appropriate judge based on language
            if contest_submission.language == 'python':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_python_fallback(
                    contest_submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            elif contest_submission.language == 'cpp':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_cpp(
                    contest_submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            elif contest_submission.language == 'java':
                stdout, stderr, verdict_for_test_case, execution_time_tc, memory_used_tc = judge_java(
                    contest_submission.code, input_data, TIME_LIMIT_SECONDS, MEMORY_LIMIT_MB
                )
            else:
                verdict_for_test_case = "runtime_error"
                stderr = "Unsupported language for judging."
            
            # Ensure status is always one of: pending, processing, finished
            contest_submission.status = 'processing'  # Keep status as processing during evaluation

            # Update verdict based on test case result
            if verdict_for_test_case in ["success", "accepted"]:
                if clean_output(stdout) == clean_output(expected_output):
                    passed_count += 1
                else:
                    verdict_for_test_case = "wrong_answer"
                    # If it's a WA, the overall verdict becomes WA unless a more severe error occurs
                    if final_verdict == "accepted":
                        final_verdict = "wrong_answer"
            else:
                # Handle various error cases
                if verdict_for_test_case == "compilation_error":
                    final_verdict = "compilation_error"
                    last_error_message = stderr
                    break # Stop evaluating further test cases for CE
                elif verdict_for_test_case == "runtime_error":
                    # Only upgrade to RE if current is AC/WA/TLE/MLE
                    if final_verdict in ["accepted", "wrong_answer", "time_limit_exceeded", "memory_limit_exceeded"]:
                        final_verdict = "runtime_error"
                        last_error_message = stderr
                    break # Stop evaluating further test cases for RE
                elif verdict_for_test_case == "time_limit_exceeded":
                    # Only upgrade if current is AC/WA
                    if final_verdict in ["accepted", "wrong_answer"]:
                        final_verdict = "time_limit_exceeded"
                        last_error_message = stderr
                elif verdict_for_test_case == "memory_limit_exceeded":
                    # Only upgrade if current is AC/WA
                    if final_verdict in ["accepted", "wrong_answer"]:
                        final_verdict = "memory_limit_exceeded"
                        last_error_message = stderr
                elif verdict_for_test_case == "wrong_answer":
                    # This case should technically be caught by "verdict_for_test_case == 'success'" logic
                    # but including for robustness.
                    if final_verdict == "accepted":
                        final_verdict = "wrong_answer"

            # Update execution metrics (take maximum values)
            contest_submission.execution_time = max(contest_submission.execution_time or 0.0, execution_time_tc)
            contest_submission.memory_used = max(contest_submission.memory_used or 0.0, memory_used_tc)

        # Final updates after all test cases
        contest_submission.status = 'finished'  # Always finished at this point
        contest_submission.test_cases_passed = passed_count
        contest_submission.total_test_cases = total_count
        contest_submission.judge_output = last_error_message

        # Set final verdict and score based on test results
        if passed_count == total_count:
            # All test cases passed, force verdict to accepted
            contest_submission.final_verdict = 'accepted'
            contest_submission.score = contest_problem.points
        else:
            # Not all test cases passed, use accumulated verdict
            contest_submission.final_verdict = final_verdict
            contest_submission.score = 0

        # Save everything at once with force_update
        contest_submission.save(force_update=True)
        
        print(f"Contest Submission {contest_submission.id} evaluation complete: "
              f"status={contest_submission.status}, "
              f"verdict={contest_submission.final_verdict}, "
              f"passed={passed_count}/{total_count}")

    except Exception as e:
        from contests.models import ContestSubmission
        print(f"Error evaluating contest submission {contest_submission_id}: {e}")
        try:
            contest_submission = ContestSubmission.objects.get(id=contest_submission_id)
            contest_submission.status = 'finished'  # Status can only be: pending, processing, finished
            contest_submission.final_verdict = 'judging_error'  # This is where error type goes
            contest_submission.judge_output = f"Judge system error: {e}"
            contest_submission.score = 0
            contest_submission.save()
        except Exception as inner_e:
            print(f"Failed to update error state for submission {contest_submission_id}: {inner_e}")

def evaluate_with_custom_input(code, input_data, language, time_limit=5, memory_limit=256):
    """
    Evaluates code with custom input without storing in database.
    Returns a dictionary with execution results.
    """
    try:
        stdout = ""
        stderr = ""
        verdict = "pending"
        execution_time = 0.0
        memory_used = 0.0

        # Run the appropriate judge based on language
        if language == 'python':
            stdout, stderr, verdict, execution_time, memory_used = judge_python_fallback(
                code, input_data, time_limit, memory_limit
            )
        elif language == 'cpp':
            stdout, stderr, verdict, execution_time, memory_used = judge_cpp(
                code, input_data, time_limit, memory_limit
            )
        elif language == 'java':
            stdout, stderr, verdict, execution_time, memory_used = judge_java(
                code, input_data, time_limit, memory_limit
            )
        else:
            verdict = "runtime_error"
            stderr = "Unsupported language for judging."

        result = {
            'stdout': stdout,
            'stderr': stderr,
            'verdict': verdict,
            'execution_time': execution_time,
            'memory_used': memory_used
        }
        
        return result

    except Exception as e:
        return {
            'stdout': '',
            'stderr': str(e),
            'verdict': 'runtime_error',
            'execution_time': 0.0,
            'memory_used': 0.0
        }

def judge_python_fallback(code, input_data, time_limit, memory_limit_mb):
    """
    Fallback function to test code execution without Docker.
    Only for debugging - NOT SECURE for production!
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            code_file_path = os.path.join(temp_dir, "solution.py")
            with open(code_file_path, "w") as f:
                f.write(code)
            
            # Run the Python script directly (NOT SECURE!)
            process = subprocess.Popen(
                [sys.executable, code_file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=time_limit)
                exit_code = process.returncode
                
                execution_time = 0.0  # Placeholder
                memory_used = 0.0  # Placeholder
                
                if exit_code == 0:
                    verdict = "success"
                else:
                    verdict = "runtime_error"
                    
                return stdout, stderr, verdict, execution_time, memory_used
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return "", "Time Limit Exceeded", "time_limit_exceeded", time_limit, 0.0
            
    except Exception as e:
        return "", f"System Error: {str(e)}", "system_error", 0.0, 0.0