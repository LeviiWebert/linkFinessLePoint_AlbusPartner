import google.generativeai as genai

# Configure the API key
genai.configure(api_key="AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o")

# Create the model
model = genai.GenerativeModel('gemini-2.5')

# Generate content
response = model.generate_content("Explain how AI works in a few words")

print(response.text)