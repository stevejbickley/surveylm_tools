# SurveyLM

SurveyLM: a platform to explore emerging value perspectives in Augmented Language Models' behaviors

## Preparation

Requirements: python(^3.10), [pyenv](https://github.com/pyenv/pyenv), [poetry](https://python-poetry.org). Currently, python 3.11.4 is used

### Navigate to the folder

Run the following if you are in a folder one above the root folder (i.e. root folder signalled by '~' below):

```cd ../panalogylab/survey```

Or alternatively, you can run the following (i.e. depending on your specific folder setup):

```cd ~/panalogylab/survey```

### Installation

Clone the project and run the following commands:

```poetry env use path_to_pyevn_python_version```

If you are not using pyenv, just replace the above command with:

```poetry env use path_to_python_interpreter```

Activate the virtual environment if needed:

```source .venv/bin/activate```

Run: 

```poetry update```

## To Run

Then Run from the root directory:

```python -m streamlit run survey/apps/streamlit/Concept.py```

## Troubleshooting

### Reset PostgreSQL Service and clear Streamlit Cache

Note, sometimes you might need to restart the PostgreSQL Server to clear any potential issues:

```brew services restart postgresql # On macOS with Homebrew```

And maybe also a good idea to clear the Streamlit cache:

```streamlit cache clear```

### Accessing and Checking the PostgreSQL log files

To check the logs, first locate the PostgreSQL log files:

1) On Linux, the logs are typically located in /var/log/postgresql/ or within the PostgreSQL data directory.

2) On macOS (installed via Homebrew), the logs are usually in /usr/local/var/postgres.

3) On Windows, the logs are typically found in the PostgreSQL installation directory, often C:\Program Files\PostgreSQL\<version>\data\pg_log.

For macos, once you have located the files, run something like the following (i.e. substitute in your actual folder path):

```tail -f /usr/local/var/postgres/server.log```

### Monitor server resources and other system monitoring tools

To monitor server resources, use system monitoring tools like the "Activity Monitor" or "Task Manager" to check CPU and RAM usage. In the command-line/terminal, you can use tools like e.g., 'top' or 'htop'. 

With macos, run the following commands to install and use/view htop:

```
brew install htop
sudo htop
```
