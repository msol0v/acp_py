# ACP Python application

## Windows setup

1. Install Python 3.10 or newer and Git.
2. Clone this repository.
3. Run `setup_venv.bat` once. It creates `.venv` and installs the dependencies from `requirements.txt`.
4. Start the application whenever needed with `run.bat`.

The virtual environment is local to this checkout and is not committed to the repository. The setup script can be run again to install or update dependencies.

## Configuration

Set the serial port for the ARINC adapter in `config.json` before starting the application (the default is `COM3`).
