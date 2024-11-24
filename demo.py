import streamlit as st
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI
from dotenv import load_dotenv
import os
from difflib import SequenceMatcher

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize session state for conversation history if not exists
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_language' not in st.session_state:
    st.session_state.current_language = None
if 'show_corrections' not in st.session_state:
    st.session_state.show_corrections = False
if 'last_text' not in st.session_state:
    st.session_state.last_text = None
if 'last_correction' not in st.session_state:
    st.session_state.last_correction = None

def transcribe_text_to_voice(audio_location):
    client = OpenAI(api_key=API_KEY)
    audio_file= open(audio_location, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcript.text

def get_grammar_correction(text, language):
    client = OpenAI(api_key=API_KEY)
    
    prompt = f"You are a language teacher. Please correct any grammar mistakes in this {language} text, but only return the corrected version without any explanations: {text}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def format_text_with_corrections(original, corrected):
    """Creates HTML with strikethrough for incorrect parts and normal text for corrections"""
    output = []
    s = SequenceMatcher(None, original, corrected)
    
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'replace':
            output.append(f"<s>{original[i1:i2]}</s> {corrected[j1:j2]}")
        elif tag == 'delete':
            output.append(f"<s>{original[i1:i2]}</s>")
        elif tag == 'insert':
            output.append(f" {corrected[j1:j2]}")
        elif tag == 'equal':
            output.append(original[i1:i2])
            
    return ''.join(output)

def chat_completion_call(text, language):
    client = OpenAI(api_key=API_KEY)
    
    # Check if language has changed
    if st.session_state.current_language != language:
        st.session_state.messages = []  # Reset conversation history
        st.session_state.current_language = language
    
    # If messages list is empty, initialize with system message
    if not st.session_state.messages:
        system_message = {"role": "system", "content": f"""You are Nasreddin Hodja, a legendary folk character known for your wit, wisdom and humor. You are a middle-aged imam wearing traditional Ottoman attire with a large turban. You speak with a mix of humor and wisdom, often using proverbs and analogies. You love telling stories that contain unexpected moral lessons.

Your responses should:
- Be playful and humorous while containing deeper wisdom
- Include relevant folk tales and proverbs when appropriate
- Sometimes start with "Ah, this reminds me of a story..." followed by a brief amusing anecdote
- Use simple language but deliver profound insights
- Occasionally mention your trusty donkey or your experiences in your village
- End with a clever twist or unexpected moral lesson
- Dont make your answers too long
- Respond entirely in {language}
- Keep in mind that your visitor is learning {language} and culture of this country.

Remember to maintain your persona as a kind-hearted trickster who teaches through humor and indirect wisdom."""}
        st.session_state.messages.append(system_message)
    
    # Add user message to history
    user_message = {"role": "user", "content": text}
    st.session_state.messages.append(user_message)
    
    # Get response from API
    response = client.chat.completions.create(
        model="gpt-4o",  # Fixed typo in model name from "gpt-4o"
        messages=st.session_state.messages
    )
    
    # Add assistant's response to history
    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
    st.session_state.messages.append(assistant_message)
    
    return response.choices[0].message.content

def text_to_speech_ai(speech_file_path, api_response):
    client = OpenAI(api_key=API_KEY)
    response = client.audio.speech.create(model="tts-1-hd",voice="fable",input=api_response)
    response.stream_to_file(speech_file_path)

def main_content():
    st.title("🧮 Nasreddin Hodja - The Witty Sage")

    # Language selection
    language = st.selectbox(
        "Choose your preferred language",
        ["Azerbaijani 🇦🇿", "Kazakh 🇰🇿", "Kyrgyz 🇰🇬", "Uzbek 🇺🇿", "Tajik 🇹🇯", "Turkish 🇹🇷", "Turkmen 🇹🇲"]
    )

    # Display video of Nasreddin Hodja character
    col1, col2 = st.columns([2,3])
    with col1:
        st.video("0.mov", start_time=0, loop=True, autoplay=True)

    with col2:
        greetings = {
            "Turkish 🇹🇷": """
            Selamün aleyküm! 🤗 Ben Nasreddin Hoca, Anadolu'nun sevilen hikaye anlatıcısı ve bilge delisiyim.
            Ses kaydediciyi tıklayın ve düşüncelerinizi paylaşın - belki de bana meşhur hikayelerimden birini hatırlatır!
            """,
            "Azerbaijani 🇦🇿": """
            Salam! 🤗 Mən Nəsrəddin Hoca, sevimli hekayəçi və müdrik dəliyəm.
            Səs yazıcısını basın və fikirlərinizi bölüşün - bəlkə də məşhur hekayələrimdən birini xatırladacaq!
            """,
            "Kazakh 🇰🇿": """
            Ассалаумағалейкум! 🤗 Мен Насреддин Қожа, сүйікті әңгімеші және дана ақымақпын.
            Дауыс жазғышты басып, ойыңызды бөлісіңіз - мүмкін бұл маған әйгілі әңгімелерімнің бірін еске түсірер!
            """,
            "Kyrgyz 🇰🇬": """
            Ассалому алейкум! 🤗 Мен Насреддин Кожо, сүйүктүү аңгемечи жана акылман келесоомун.
            Үн жаздыргычты басып, ойлоруңузду бөлүшүңүз - балким бул мага атактуу аңгемелеримдин бирин эстетер!
            """,
            "Uzbek 🇺🇿": """
            Assalomu alaykum! 🤗 Men Nasriddin Afandi, sevimli hikoyachi va dono tentagiman.
            Ovoz yozgichni bosing va fikrlaringizni ulashing - balki bu menga mashhur hikoyalarimdan birini eslatib qo'yar!
            """,
            "Tajik 🇹🇯": """
            Ассалому алейкум! 🤗 Ман Насриддин Афандӣ, ҳикоягӯй ва хирадманди дӯстдоштанӣ ҳастам.
            Сабткунандаи садоро пахш кунед ва андешаҳои худро бо мо бо мо ҳамрох кунед - шояд ин маро ба яке аз ҳикояҳои машҳурам ёдовар шавад!
            """,
            "Turkmen 🇹🇲": """
            Essalawmaleýkim! 🤗 Men Nasreddin Hoja, söýgüli hekaýaçy we paýhasly dälisi.
            Ses ýazgyjyny basyň we pikirlerinizi paýlaşyň - belki-de bu maňa meşhur hekaýalarymiň birini ýatladar!
            """
        }
        st.markdown(greetings[language])
        initial_greeting = greetings[language]
        speech_file_path = 'greeting.mp3'
        text_to_speech_ai(speech_file_path, initial_greeting)
        st.audio(speech_file_path)

    # Record audio
    audio_bytes = audio_recorder()
    if audio_bytes:
        audio_location = "audio_file.wav"
        with open(audio_location, "wb") as f:
            f.write(audio_bytes)

        text = transcribe_text_to_voice(audio_location)
        st.write("Your message:")
        st.write(text)
        
        # Store the text for grammar correction panel
        st.session_state.last_text = text
        st.session_state.last_correction = get_grammar_correction(text, language)
        st.session_state.show_corrections = True

        api_response = chat_completion_call(text, language)
        st.write("Nasreddin's response:")
        st.write(api_response)

        speech_file_path = 'audio_response.mp3'
        text_to_speech_ai(speech_file_path, api_response)
        st.audio(speech_file_path)

def grammar_sidebar():
    with st.sidebar:
        st.title("Grammar Corrections")
        st.markdown("Here you can see grammar corrections for your messages.")
        
        if st.session_state.show_corrections and st.session_state.last_text and st.session_state.last_correction:
            if st.session_state.last_text != st.session_state.last_correction:
                st.markdown("### Your original text:")
                st.markdown(f"*{st.session_state.last_text}*")
                
                st.markdown("### Correction:")
                st.markdown(format_text_with_corrections(
                    st.session_state.last_text, 
                    st.session_state.last_correction
                ), unsafe_allow_html=True)
            else:
                st.markdown("### No corrections needed!")
                st.markdown("Your grammar was perfect! 👏")
                st.markdown(f"*{st.session_state.last_text}*")
        else:
            st.markdown("Record a message to see grammar corrections here!")

# Add this at the bottom of the file
if __name__ == "__main__":
    grammar_sidebar()
    main_content()
