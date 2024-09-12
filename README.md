# SurveyLM-Agent-Profile-Generator
A Python-based tool for generating synthetic agent profiles for SurveyLM.

## Preparation
 
# Navigate to the folder

```cd ./surveylm_tools```

# Clone the project and run the following commands:

```poetry env use path_to_pyevn_python_version```

# If you are not using pyenv, just replace the above command with:

```poetry env use path_to_python_interpreter```

# Activate the "agent_generator" virtual environment if needed:

```source ./.venv/bin/activate```


# Next, run the following to update poetry and install ffmpeg (if required):

```poetry update```

Macos
```brew install ffmpeg```

Linux
```apt install ffmpeg```

Running Python and Scripts:

```poetry run python script.py```

# Note: ffmpeg is open-source suite of libraries and programs for handling video, audio, and other multimedia files and streams


## Creating your own poetry environment

# To create new poetry project (if required):

```poetry init```


# To add a new package to your project, use:

```poetry add package-name```

# Or alternative, a sub-environment/package (if required): 

```poetry new agent_generator```

# Initialize the existing directory (if required):

```cd agent_generator``` 

# followed by:

```poetry init```

# and:

```poetry update```



