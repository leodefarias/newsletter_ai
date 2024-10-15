import streamlit as st
from newsletter_gen.crew import NewsletterGenCrew
import os

class NewsletterGenUI:

    def load_html_template(self):
        with open("src/newsletter_gen/config/newsletter_template.html", "r") as file:
            html_template = file.read()

        return html_template

    def generate_newsletter(self, topic, personal_message):
        inputs = {
            "topic": topic,
            "personal_message": personal_message,
            "html_template": self.load_html_template(),
        }
        crew = NewsletterGenCrew()
        crew_output = crew.crew().kickoff(inputs=inputs)

        # Attempt to read the generated file content
        try:
            # Use the file path stored in crew.newsletter_output_file
            newsletter_file = crew.newsletter_output_file

            # Check if the file exists
            if os.path.exists(newsletter_file):
                with open(newsletter_file, 'r', encoding='utf-8') as f:
                    newsletter_content = f.read()
            else:
                st.error("Newsletter file not found.")
                newsletter_content = ""

        except (FileNotFoundError, AttributeError):
            st.error("Unable to generate the newsletter content.")
            newsletter_content = ""

        return newsletter_content

    def newsletter_generation(self):

        if st.session_state.generating:
            st.session_state.newsletter = self.generate_newsletter(
                st.session_state.topic, st.session_state.personal_message
            )

        if st.session_state.newsletter and st.session_state.newsletter != "":
            with st.container():
                st.write("Newsletter successfully generated!")

                # Download button
                st.download_button(
                    label="Download HTML file",
                    data=st.session_state.newsletter,
                    file_name="newsletter.html",
                    mime="text/html",
                )
            st.session_state.generating = False

    def sidebar(self):
        with st.sidebar:
            st.title("Newsletter Generator")

            st.write(
                """
                To generate a newsletter, enter a topic and a personal message. \n
                Your AI agent team will generate a newsletter for you!
                """
            )

            st.text_input("Topic", key="topic", placeholder="US Stock Market")

            st.text_area(
                "Your personal message (to include at the top of the newsletter)",
                key="personal_message",
                placeholder="Dear readers, welcome to the newsletter!",
            )

            if st.button("Generate Newsletter"):
                st.session_state.generating = True

    def render(self):
        st.set_page_config(page_title="Newsletter Generation", page_icon="📧")

        if "topic" not in st.session_state:
            st.session_state.topic = ""

        if "personal_message" not in st.session_state:
            st.session_state.personal_message = ""

        if "newsletter" not in st.session_state:
            st.session_state.newsletter = ""

        if "generating" not in st.session_state:
            st.session_state.generating = False

        self.sidebar()

        self.newsletter_generation()

if __name__ == "__main__":
    NewsletterGenUI().render()
