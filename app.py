import streamlit as st
from groq import Groq
import base64
import os
from dotenv import load_dotenv
import json
load_dotenv()
# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Function to check if the file is remote (URL)
def is_remote_file(file_path):
    return file_path.startswith("http://") or file_path.startswith("https://")

# Function to process image and extract markdown content from Together AI API
def get_markdown(file_path):
    system_prompt = """
    Convert the provided image into Markdown format. Ensure that all content from the page is included, such as headers, footers, subtexts, images (with alt text if possible), tables, and any other elements.

    Requirements:
    - Output Only Markdown: Return solely the Markdown content without any additional explanations or comments.
    - No Delimiters: Do not use code fences or delimiters like markdown.
    - Complete Content: Do not omit any part of the page, including headers, footers, and subtext.
    """

    if is_remote_file(file_path):
        final_image_url = file_path
    else:
        final_image_url = f"data:image/jpeg;base64,{encode_image(file_path)}"
        
    client = Groq(api_key=os.getenv("api_key"))
    
    message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {"type": "image_url", "image_url": {"url": final_image_url}},
                ],
            }
        ]

    response = client.chat.completions.create(model="llama-3.2-90b-vision-preview", messages=message)
    
    return response.choices[0].message.content


def get_details(markdown_text):
    
    output_json = {
        "documen_type":"",
        "certificate_holder_name":"",
        "authorizer_name":"",
        "credict_type":"",
        "provider":"",
        "details":[
            {"title":"",
            "total_credit":"",
            "issue_date":""}
            ]
    }
    system_prompt = f"""
    Work as expert in parsing the document parse the following document.
    content :{markdown_text}
    Requirements:
    - output json Format {output_json}
    - if document is transcript give the each course details list format.
    - Do NOT add any other details json other than provided json format.
    - Total credict is only credict point no text details.
    - Classify the document type as only in transcript, certificate.
    - Output Only json as an format: Return solely the json without any additional explanations or comments.

    """
        
    client = Groq(api_key=os.getenv("api_key"))
    
    messages = [{"role": "user", "content": system_prompt}]

    llm = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format={"type": "json_object"}
    )
    

    
    return llm.choices[0].message.content

# Streamlit App
st.title("OCR with Together AI")
uploaded_file = st.file_uploader("Upload an Image File")
remote_url = st.text_input("Or Enter Remote File URL")

if st.button("Process Image"):
    if not uploaded_file and not remote_url:
        st.error("Please upload an image file or provide a remote URL.")
    else:
        try:
            if uploaded_file:
                # Save uploaded file temporarily
                file_path = os.path.join("/tmp", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())
            else:
                file_path = remote_url

            # Get the Markdown output from Together AI
            markdown_content = get_markdown(file_path)
            
            # Display the Markdown content
            st.success("Image processed successfully.")
            st.markdown(markdown_content)
            st.success("Parsed Content")
            parsed_response = get_details(markdown_text=markdown_content)
            st.json(json.loads(parsed_response))

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

