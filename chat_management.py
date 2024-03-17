from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer, KafkaConsumer
import logging
from textual.logging import TextualHandler

# Logger configuration
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
handler = TextualHandler()
handler.setFormatter(formatter)
logger = logging.getLogger("Chat Management")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

import os


#------------------------------->
#       Kafka Configurations
#------------------------------->
# Define the name of the environment variable
env_variable_name = "OTBROKER"

# Check if the environment variable exists
if env_variable_name in os.environ:
    # Use the value of the environment variable
    bootstrap_servers = os.getenv(env_variable_name)
else:
    # Use a default value
    bootstrap_servers = "localhost:9092"
    
num_partitions = 1
replication_factor = 1

USER_NAME_PREFIX = 'OTUser__'
GROUP_NAME_PREFIX = 'OTGroup__'

#------------------------------->
#       Utility Methods
#------------------------------->
def filter_strings_by_starting_substring(strings, substring):
    """Filter strings based on starting substring."""
    return [s.replace(substring, '') for s in strings if substring in s]



#------------------------------->
#       Kafka Admin Client
#------------------------------->
admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)

#------------------------------->
#       Kafka Methods
#------------------------------->
def get_all_topics():
    """Retrieve all topic names."""
    # Retrieve metadata about all topics
    topics = admin_client.list_topics()
    return filter_strings_by_starting_substring(topics, "OTGroup__")

def create_topic(topic_name):
    """Create a Kafka topic."""
    # Create a topic with the user's name
    topic_name = f"{GROUP_NAME_PREFIX}{topic_name}"
    current_topics = get_all_topics()
    if topic_name in current_topics:
        error = f"Topic {topic_name} already exists"
        logger.error(f"Topic {topic_name} already exists")
        return False, error
    else:
        new_topic = NewTopic(topic_name, num_partitions, replication_factor)
        admin_client.create_topics([new_topic])
        logger.info(f"Topic {topic_name} created successfully.")
        return True, None
    

def send_message_to_topic(topic, username, message):
    """Send a message to a Kafka topic."""
    # Configure Kafka producer
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    try:
        # Construct the message to send
        formatted_message = f"{username}: {message}"
        
        # Send the message to the Kafka topic
        producer.send(topic, formatted_message.encode('utf-8'))
        logger.info("Message sent successfully.")

    except Exception as e:
        logger.error(f"Error: {e}")

    finally:
        # Close the producer
        producer.close()

def get_msgs_for_topic(topic, username):
    """Retrieve messages for a given topic."""
    # Configure Kafka consumer
    group_id = f"{USER_NAME_PREFIX}{username}"  # Using username as consumer group
    consumer = KafkaConsumer(
        topic,
        auto_offset_reset='earliest',
        group_id=group_id,
        bootstrap_servers=[bootstrap_servers]
    )

    messages = []
    try:
        # Start consuming messages
        msg_pack = consumer.poll(timeout_ms=500)
        for _, records in msg_pack.items():
            for message in records:
                messages.append(message.value.decode('utf-8'))

    except Exception as e:
        logger.error(f"Error: {e}")

    finally:
        # Close the consumer
        consumer.close()
        if len(messages) > 0:
            return '\n'.join(messages)
        else:
            return None

def remove_topic(topic):
    """Remove a Kafka topic."""
    # Delete the topic
    admin_client.delete_topics([f"{GROUP_NAME_PREFIX}{topic}"])
    logger.info(f"Topic '{topic}' removed successfully.")




if __name__ == "__main__":
    pass
