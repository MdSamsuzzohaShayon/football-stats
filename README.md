# Project Setup and Requirements
This guide provides instructions for setting up the project environment, installing dependencies, and configuring database connections on a Linux system.

## Prerequisites
 - **Python 3:** Ensure Python 3 is installed on your machine.
 - **MySQL and Redis:** You’ll need to have both MySQL and Redis servers installed and running.

## Steps to Get Started
 1. Create and Activate a Python Virtual Environment: It’s recommended to use a virtual environment to manage dependencies. Follow these commands to set up and activate the environment:

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
 2. Install Required Packages: Once the virtual environment is active, install the necessary packages listed in requirements.txt:
   ```
   pip install -r requirements.txt
   ```
 3. Start and Connect MySQL and Redis: Before starting the application, ensure MySQL and Redis servers are running and connected. 
      - **MySQL:** If you’re using the LAMPP server on Linux, start the MySQL server with:
    
         ```
         sudo /opt/lampp/lampp start
         ``` 
      - **Redis:** Install Redis if not already installed (installation guide), and start the Redis server with:

         ```
         sudo systemctl start redis
         ```
 4. Start the FastAPI Server: With the databases running, you can now start the FastAPI server:
   ```
   python3 -m src.main
   ```
 5. Configuration: If you need to modify your database credentials or connection settings, navigate to the src/config folder. Update the configuration files as necessary to match your setup.
 6. Seed: We can seed some dummy data
   ```
   python3 -m src.seeds
   ```




#### Left
 - Need to send message to all users
 - Need to cache favorite match properly
 - Pub/Sub for the match
 - Creating Frontend for this