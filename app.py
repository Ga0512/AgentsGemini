import streamlit as st
import pandas as pd
from llama_parse_data import llama_parse_md
from query_data import main

# Funções para carregar e salvar usuários
def load_users():
    return pd.read_csv('users.csv')

def authenticate(username, password, users_df):
    user_row = users_df[users_df['username'] == username]
    if not user_row.empty and user_row.iloc[0]['password'] == password:
        agents = user_row.iloc[0]['agents']
        if pd.notna(agents) and agents:
            return True, agents.split('|')
        else:
            return True, []
    return False, []

def save_users(users_df):
    users_df.to_csv('users.csv', index=False)

# Carrega os usuários
users_df = load_users()

# Título do aplicativo
st.title('AgentsGemini ✨')

# Verifica se o usuário está autenticado
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'page' not in st.session_state:
    st.session_state.page = 'Login'

if not st.session_state.authenticated:
    if st.session_state.page == 'Login':
        st.sidebar.title('Login')
        username = st.sidebar.text_input('Username')
        password = st.sidebar.text_input('Password', type='password')
        if st.sidebar.button('Login'):
            authenticated, user_agents = authenticate(username, password, users_df)
            if authenticated:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_agents = user_agents
                st.session_state.page = 'Navigation'
                st.experimental_rerun()
            else:
                st.error('Username or password is incorrect')
        if st.sidebar.button('Go to Register'):
            st.session_state.page = 'Register'
            st.experimental_rerun()
        st.stop()

    elif st.session_state.page == 'Register':
        st.sidebar.title('Register')
        new_username = st.sidebar.text_input('New Username')
        new_password = st.sidebar.text_input('New Password', type='password')
        if st.sidebar.button('Register'):
            if new_username in users_df['username'].values:
                st.error('Username already exists. Please choose another one.')
            else:
                new_user = pd.DataFrame({'username': [new_username], 'password': [new_password], 'agents': ['']})
                users_df = pd.concat([users_df, new_user], ignore_index=True)
                save_users(users_df)
                st.success('Registration successful! Please log in.')
                st.session_state.page = 'Login'
                st.experimental_rerun()
        if st.sidebar.button('Go to Login'):
            st.session_state.page = 'Login'
            st.experimental_rerun()
        st.stop()

elif st.session_state.page == 'Navigation':
    st.sidebar.title('Logout')
    if st.sidebar.button('Logout'):
        st.session_state.authenticated = False
        st.session_state.username = ''
        st.session_state.user_agents = []
        st.session_state.page = 'Login'
        st.experimental_rerun()

    st.sidebar.title('Navigation')
    pagina = st.sidebar.radio('Pages', ['Create Agent', 'Chat'])

    if pagina == 'Create Agent':
        st.header('Create Agent')

        uploaded_files = st.file_uploader("Upload files", type=['txt', 'pdf', 'xlsx', 'pptx', 'md'], accept_multiple_files=True)
        agent_name = st.text_input('Agent', 'MyAgent')
        llamaparse_api_key = st.text_input('LlamaParse API key', type='password')
        openai_api_key = st.text_input('OpenAI API key (for embedding)', type='password')

        if st.button('Create Agent'):
            if uploaded_files:
                datas = []
                for file in uploaded_files:
                    with open(file.name, 'wb') as f:
                        f.write(file.getbuffer())
                    datas.append(file.name)
                with st.spinner('processing...'):
                    llama_parse_md(datas, agent_name, llamaparse_api_key, openai_api_key)
                st.success('Agent created!')

                # Adiciona o novo agente à lista de agentes do usuário
                st.session_state.user_agents.append(agent_name)
                users_df.loc[users_df['username'] == st.session_state.username, 'agents'] = '|'.join(st.session_state.user_agents)
                save_users(users_df)
            else:
                st.error("Please upload at least one file.")

    elif pagina == 'Chat':
        st.header('Chat')
        agent_name = st.selectbox('Select the Agent', st.session_state.user_agents)
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        openai_api_key = st.text_input('OpenAI API key (for semantic search)', type='password')
        google_api_key = st.text_input('Google Studio API Key', type='password')

        user_input = st.text_input('How can the agent help you?', key='query_input')

        if st.button('Send'):
            with st.spinner('Processing...'):
                response = main(user_input, agent_name, openai_api_key, google_api_key)
            st.session_state.chat_history.append({'user': user_input, 'agent': response})
            st.experimental_rerun()

        st.write('Chat:')
        for chat in st.session_state.chat_history:
            st.write(f"You: {chat['user']}")
            st.write(f"{agent_name}: {chat['agent']}")

        if st.button('Clean Chat'):
            st.session_state.chat_history = []
            st.experimental_rerun()

