import threading
import time
import chat_management
import re

from textual import events, on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.validation import Function, Number, Validator, ValidationResult
from textual.widgets import Button, Header, Input, Label, Pretty, RadioButton, RadioSet, Static, TextArea, Tree


ACTIVE_USER="Default_User"
def check_alphanumeric_no_spaces(input_string):
    """
    Check if the input string contains only alphanumeric characters and no spaces.

    Args:
        input_string (str): The input string to be checked.

    Returns:
        bool: True if the input string contains only alphanumeric characters and no spaces, False otherwise.
    """
    # Define the regex pattern
    pattern = r'^[A-Za-z0-9]+$'
    
    # Check if the input string matches the pattern
    if re.match(pattern, input_string):
        return True
    else:
        return False
    
class DeleteTopicScreen(ModalScreen[bool]):
    """Modal screen for confirming topic deletion."""

    def __init__(self, topic: str):
        """
        Initialize the DeleteTopicScreen.

        Args:
            topic (str): The topic to be deleted.
        """
        self.topic = topic
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Compose the UI elements for the delete topic screen.

        Returns:
            ComposeResult: The composed UI elements.
        """
        with Container():
            yield Label(f"Are you sure you want to remove {self.topic}?")
            with Horizontal():
                yield Button("No", id="no", variant="error")
                yield Button("Yes", id="yes", variant="success")

    @on(Button.Pressed, '#yes')
    def remove_topic(self) -> None:
        """
        Handle the button press event to remove the topic.
        """
        chat_management.remove_topic(self.topic)
        self.dismiss(True)

    @on(Button.Pressed, '#no')
    def exit(self) -> None:
        """
        Handle the button press event to exit without removing the topic.
        """
        self.dismiss(False)


class CreateTopic(ModalScreen[str]):
    """Screen with a dialog to create a new topic."""
    topic_failure_label = Label("", id="topic_failure_label")
    def compose(self) -> ComposeResult:
        """
        Compose the UI elements for creating a new topic dialog.

        Returns:
            ComposeResult: The composed UI elements.
        """
        self.create_topic_input = Input(
            id="create_topic_input",
            placeholder="Enter a topic name.",
            validators=[Function(check_alphanumeric_no_spaces, "Topic name contains invalid characters.")],
        )

        yield Header()
        yield self.topic_failure_label
        yield Vertical(self.create_topic_input, id="dialog1")
        yield Horizontal(
            Horizontal(
                Button("Create", variant="success", id="create"),
                Button("Cancel", variant="primary", id="cancel"),
                id="topic_btns"
            ),
            id="dialog",
        )
    @on(Button.Pressed,'#create')
    async def create(self, event: Button.Pressed) -> None:
        """
        Handles the create method for creating a topic.

        Args:
            event (Button.Pressed): The button press event.
        """
        topic = self.create_topic_input.value
        if ' ' in topic or len(topic) == 0:
            self.topic_failure_label.update(f"Topic '{topic}' is invalid.")
            return
        else:
            result, msg = chat_management.create_topic(topic)
            if result:
                self.dismiss(self.query_one(Input).value)
            else:
                self.topic_failure_label.update(msg)
                return
                
    @on(Button.Pressed, '#cancel')
    async def cancel(self, event: Button.Pressed) -> None:
        """
        Handles the create method for creating a topic.

        Args:
            event (Button.Pressed): The button press event.
        """
        self.dismiss()

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        """
        Show invalid reasons for the input field.

        Args:
            event (Input.Changed): The input changed event.
        """
        if not event.validation_result.is_valid:
            self.topic_failure_label.update(str(event.validation_result.failure_descriptions))
        else:
            self.topic_failure_label.update()

    @on(Input.Submitted)
    async def create_topic(self, event: Input) -> None:
        """
        Handle input submission events.

        Args:
            event (Input): The input submission event.
        """
        if len(event.value) == 0:
            self.app.pop_screen()

        topic = event.value
        if ' ' in topic or len(topic) == 0:
            self.topic_failure_label.update(f"Topic '{topic}' is invalid.")
            return
        else:
            result, msg = chat_management.create_topic(topic)
            self.dismiss(self.query_one(Input).value)

    async def on_key(self, event: events.Key) -> None:
        """
        Handle keyboard events.

        Args:
            event (events.Key): The keyboard event.
        """
        if event.key == "escape":
            # Handle ESC key press here, e.g., close the modal
            self.dismiss()
        else:
            # Let the superclass handle other key events
            await super()._on_key(event)
class ChatWindow(Screen):
    """Class to manage chat functionality."""

    SELECTED_TOPIC = None
    SELECTED_NODE = None
    MESSAGES = {}

    def __init__(self, user_name: str):
        """
        Initialize ChatManager.

        Args:
            user_name (str): The username of the chat user.
        """
        self.user_name = user_name
        super().__init__()
        # Start a background thread for message fetching
        self.kafka_thread = threading.Thread(target=self.fetch_messages_from_kafka)
        self.kafka_thread.daemon = True
        self.kafka_thread.start()
    
    def build_topic_tree(self) -> Tree[dict]:
        """
        Build the topic tree based on active topics.

        Returns:
            Tree[dict]: A tree structure representing the topics.
        """
        # Set up Topics
        topic_list: Tree[dict] = Tree("Topics", id="group_tree")
        active_topics = chat_management.get_all_topics()
        topic_list.root.expand()
        topic_list.guide_depth = 1
        should_expand = len(active_topics) > 0
        topic_list.expand = should_expand
        for group in active_topics:
            topic_list.root.add_leaf(group)
            self.MESSAGES[group] = self.MESSAGES.get(group,"")
        return topic_list
        
    def compose(self):
        """
        Compose the UI components and yield the results.

        Yields:
            ComposeResult: A result of UI composition.
        """
        self.title = f"Signed in as {self.user_name}"
        self.text_area = TextArea()
        self.input_area = TextArea(id="bottom-right-final")
        self.topic_list = self.build_topic_tree()


        yield Header()

        with Container(id="app-grid"):
            with VerticalScroll(id="left-pane"):
                yield self.topic_list
            with Horizontal(id="top-right"):
                yield self.text_area
            with Container(id="bottom-right"):
                yield self.input_area
            yield Button("Create Topic", variant="error", id="create_topic_btn")
            yield Button("Send", variant="primary", id="send_btn")

        self.topic_list.refresh()

    def create_topic_model_callback(self, result: str) -> None:
        """
        Handle the modal result by adding it to the topic list.

        Args:
            result (str): The result of the modal.
        """
        node = self.topic_list.root.add_leaf(result)
        self.MESSAGES[result] = self.MESSAGES.get(result,"")
        node._selected_=True
        self.SELECTED_NODE = node
        self.SELECTED_TOPIC = result


        

    def delete_topic_modal_callback(self, result: bool) -> None:
        """
        Handle the modal result by deleting the topic and its associated messages.

        Args:
            result (bool): The result of the modal.
        """
        if result:
            self.SELECTED_NODE.remove()
            self.MESSAGES.pop(self.SELECTED_TOPIC)
            self.SELECTED_TOPIC = None
            self.text_area.clear()

    def fetch_messages_from_kafka(self):
        """
        Continuously fetch messages from Kafka and update the UI.

        This method runs indefinitely in a loop, checking for new messages related to the selected topic
        and updating the UI accordingly.
        """
        while True:
            if self.SELECTED_TOPIC:
                messages = self.MESSAGES.get(self.SELECTED_TOPIC, "")
                new_messages = chat_management.get_msgs_for_topic(self.SELECTED_TOPIC, self.user_name)
                if new_messages:
                    messages += f"{new_messages}\n"
                    self.MESSAGES[self.SELECTED_TOPIC] = messages
                    self.text_area.load_text(messages)
            time.sleep(0.1)  # Sleep and fetch more messages.

    @on(Tree.NodeSelected)
    def select_topic(self, event: Tree.NodeSelected) -> None:
        """
        Handle the selection of a topic from the topic tree.

        Args:
            event (Tree.NodeSelected): The event object containing information about the selected node.
        """
        self.SELECTED_TOPIC = str(event.node.label)
        self.SELECTED_NODE = event.node
        self.text_area.load_text(self.MESSAGES.get(self.SELECTED_TOPIC, ""))

    @on(Button.Pressed, '#create_topic_btn')
    def create(self) -> None:
        """Handle the button press event to create a new topic."""
        self.app.push_screen(CreateTopic(), self.create_topic_model_callback)

    @on(Button.Pressed, '#send_btn')
    def send(self, event: Button.Pressed) -> None:
        """Handle the button press event to send a message."""
        if self.SELECTED_TOPIC:
            message = str(self.input_area.text)
            chat_management.send_message_to_topic(self.SELECTED_TOPIC, self.user_name, message)
            self.input_area.clear()
        else:
            print("No topic selected!")

    async def on_key(self, event: events.Key) -> None:
        """
        Handle keyboard events, specifically the 'backspace' key.

        Args:
            event (events.Key): The key event object.
        """
        if event.key == "backspace":
            # Handle 'backspace' key press, e.g., open a modal to delete the selected topic
            if self.topic_list.has_focus:
                self.app.push_screen(DeleteTopicScreen(self.SELECTED_TOPIC), self.delete_topic_modal_callback)
        else:
            # Let the superclass handle other key events
            await super()._on_key(event)
            
    


       
class Off_Topic(App):
    logo = '''
   ___   __  __     _____           _         ____ _           _   
  / _ \ / _|/ _|   |_   _|__  _ __ (_) ___   / ___| |__   __ _| |_ 
 | | | | |_| |_ _____| |/ _ \| '_ \| |/ __| | |   | '_ \ / _` | __|
 | |_| |  _|  _|_____| | (_) | |_) | | (__  | |___| | | | (_| | |_ 
  \___/|_| |_|       |_|\___/| .__/|_|\___|  \____|_| |_|\__,_|\__|
                             |_|                                   

'''
    CSS_PATH = "style.tcss"
    failure_label = Label(id='failure_label')

    def compose(self) -> ComposeResult:
        """
        Compose the application's user interface.

        Returns:
            ComposeResult: The composed UI elements.
        """
        with Container(id="username_prompt_container"):
            yield Label(self.logo, id="logo")
            yield Input(id="username",
                        placeholder="Username",
                        validators=[
                            Function(check_alphanumeric_no_spaces, "Username contains invalid characters."),
                        ],
                        )
            yield self.failure_label

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        """
        Show invalid reasons for the input field.

        Args:
            event (Input.Changed): The input changed event.
        """
        if not event.validation_result.is_valid:
            self.failure_label.update(str(event.validation_result.failure_descriptions))
        else:
            self.failure_label.update()

    @on(Input.Submitted)
    def get_user_name(self):
        """
        Get the user's name from the input field and push the ChatWindow screen.
        """
        name = self.query_one(Input).value
        if ' ' in name:
            self.failure_label.update(f"User name '{name}' is invalid.")
            return
        self.push_screen(ChatWindow(name))




if __name__ == "__main__":
    app = Off_Topic()
    app.run()