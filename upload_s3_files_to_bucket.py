import os
import boto3
import logging
import threading
import queue
import datetime
from botocore.exceptions import NoCredentialsError

# Get the current date
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# Define the directory where the script is located,
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
INFO_LOG_FILE = os.path.join(LOG_DIR, f"upload_info_{current_date}.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, f"upload_error_{current_date}.log")


# Create a logging queue and a logger
log_queue = queue.Queue()
logger = logging.getLogger(__name__)

# Set up a stream handler for immediate console output
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)


# Define an asynchronous log handler using threading
class AsyncLogHandler(threading.Thread):
    """
    A custom log handler that processes log messages asynchronously
    using a separate thread.

    This class inherits from `threading.Thread` and is designed to handle
    logging in a non-blocking manner.
    It reads log records from a queue and writes them to separate log files
    based on their severity levels.
    Log records with 'ERROR' level are written to an error log file, while all
    other records are written to an info log file.

    Attributes:
    log_queue (queue.Queue): A queue that holds log records to be processed.
    info_log_file (str): File path for the info log file.
    error_log_file (str): File path for the error log file.

    Methods:
    run: Continuously processes log records from the queue
    until it receives a `None` signal.
    write_log: Writes a log record to the appropriate
    log file based on its level.
    format: Formats a log record into a string.

    Usage:
    This class is intended to be used with a logging queue. It should be
    initialized with the log queue and file paths for info and error logs.
    After initialization, it starts running in a separate thread.
    """

    def __init__(self, log_queue, info_log_file, error_log_file):
        """
        Initializes the AsyncLogHandler.

        Parameters:
        log_queue (queue.Queue): The queue from which to read log messages.
        info_log_file (str): The file path to write info level logs.
        error_log_file (str): The file path to write error level logs.
        """
        super().__init__()
        self.log_queue = log_queue
        self.info_log_file = info_log_file
        self.error_log_file = error_log_file
        self.daemon = True
        self.start()

    def run(self):
        """
        Runs the thread that processes log messages from the queue.

        Continuously retrieves and processes log messages from the log queue
        until it receives a `None` to terminate.
        """
        while True:
            record = self.log_queue.get()
            if record is None:  # None is the signal to terminate
                break
            self.write_log(record)
            self.log_queue.task_done()

    def write_log(self, record):
        """
        Writes a log record to the designated log file.

        Parameters:
        record (dict): A dictionary representing a log record.

        Depending on the level of the log record, it is written to either
        the info log file or the error log file.
        """
        if record["levelname"] == "ERROR":
            log_file = self.error_log_file
        else:
            log_file = self.info_log_file
        with open(log_file, "a") as f:
            f.write(self.format(record) + "\n")

    def format(self, record):
        """
        Formats a log record into a string for writing to the log file.

        Parameters:
        record (dict): A dictionary representing a log record.

        Returns:
        str: The formatted log record as a string.
        """
        return f"{record['asctime']} - {record['levelname']} - {record['message']}"


# Start the asynchronous log handler
async_handler = AsyncLogHandler(log_queue, INFO_LOG_FILE, ERROR_LOG_FILE)


def log_async(level, msg):
    log_entry = {
        "asctime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
        "levelname": level,
        "message": msg,
    }
    log_queue.put(log_entry)


def upload_directory_to_s3(local_directory, bucket_name):
    """
    Uploads all files from a specified local directory
    to a specified AWS S3 bucket.

    This function walks through each file in the provided local directory
    and uploads it to the specified S3 bucket.
    It logs the status of each file upload,
    capturing any errors encountered during the process.

    Parameters:
    local_directory (str): The path to the local directory
    containing files to upload.
    bucket_name (str): The name of the target AWS S3 bucket.

    Returns:
    None. The function logs messages to indicate the status of file uploads.

    Raises:
    FileNotFoundError: If a file in the directory
    does not exist at the time of upload.
    NoCredentialsError: If AWS credentials are not available,
    stopping further uploads.
    Exception: Catches and logs any other exceptions during file uploads.
    """
    # Initialize S3 client
    s3 = boto3.client("s3")

    # Walk through each file in the directory
    for subdir, dirs, files in os.walk(local_directory):
        for file in files:
            try:
                full_path = os.path.join(subdir, file)
                with open(full_path, "rb") as data:
                    s3.upload_fileobj(data, bucket_name, file)
                log_async("INFO", f"File {file} uploaded to {bucket_name}")
                print(f"File {file} uploaded to {bucket_name}")
            except FileNotFoundError:
                log_async(
                    "ERROR", f"The file {file} was not found"
                )  # If the file moved or removed during the proccess
            except NoCredentialsError:
                log_async("ERROR", "Credentials not available")
                break
            except Exception as e:
                logger.error(f"Error uploading file {file}: {e}")
    async_handler.log_queue.put(None)


# Example usage
upload_directory_to_s3("./test_files", "lior-kovtun-bucket-test-two")
