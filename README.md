# CSCI6010-BigData-Tutorial

# Off-Topic Chat System

The Off-Topic Chat System is a chat application built to demonstrate basic features of Apache Kafka. It utilizes the producer and consumer model to provide chat mechanisms for users to subscribe to topics and share messages.

## Getting Started

To start the Off-Topic Chat System, follow these steps:

1. **Start Kafka Services:**
   - Ensure you have Docker Compose installed on your system.
   - Run the following command to start the Kafka services using Docker Compose:
     ```bash
     docker-compose up -d
     ```

2. **Setup Environment:**
   - Create a virtual environment for the application.
   - Install the required dependencies listed in `requirements.txt`:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```

3. **Run the Application:**
   - Run the Off-Topic Chat System using the following command:
     ```bash
     python3 off_topic.py
     ```

## Features

- **Create Topic Button:**
  - Allows users to create a new topic for communication.

- **Send Button:**
  - Sends the message provided in the text panel to the selected topic.

- **Left Panel:**
  - Displays the available topics for communication.

- **Top Right Window:**
  - Shows the messages exchanged in the selected topic.