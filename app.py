from dotenv import load_dotenv
import json
import logging
import logging.config
import os
import re
from services import bedrock_agent_runtime
from services.auth import GoogleWorkspaceAuth, init_auth_state, check_auth, login, logout
import streamlit as st
import uuid
import yaml

load_dotenv()

# Configure logging using YAML
if os.path.exists("logging.yaml"):
    with open("logging.yaml", "r") as file:
        config = yaml.safe_load(file)
        logging.config.dictConfig(config)
else:
    # Python 3.10 compatibility fix - getLevelNamesMapping doesn't exist in 3.10
    log_level_name = os.environ.get("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name)
    logging.basicConfig(level=log_level)

logger = logging.getLogger(__name__)

# Get config from environment variables
agent_id = os.environ.get("BEDROCK_AGENT_ID")
agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")  # TSTALIASID is the default test alias ID
ui_title = os.environ.get("BEDROCK_AGENT_TEST_UI_TITLE", "123RF knowledge base")
ui_icon = os.environ.get("BEDROCK_AGENT_TEST_UI_ICON")


def init_session_state():
    """Initialize session state for chat"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'citation_nums' not in st.session_state:
        st.session_state.citation_nums = []
    if 'citations' not in st.session_state:
        st.session_state.citations = []
    if 'titan_citation_style' not in st.session_state:
        st.session_state.titan_citation_style = False
    if 'trace' not in st.session_state:
        st.session_state.trace = {}

def render_login_page():
    """Render the login page"""
    st.title("Hi !")
    # st.write("Please log in with your Google Workspace account to continue.")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        auth = GoogleWorkspaceAuth()
        if st.button("Login"):
            flow = auth.create_oauth_flow()
            auth_url, _ = flow.authorization_url(prompt='select_account')
            st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#4285f4;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">Continue with Google</button></a>', 
                      unsafe_allow_html=True)

def render_main_app(user_info):
    """Render the main application"""
    st.title(ui_title)
    
    init_session_state()

    # Show user info and logout button in sidebar
    with st.sidebar:
        col1, col2 = st.columns([1, 3])
        with col1:
            # Use default icon if user doesn't have a picture
            user_picture = user_info.get('picture')
            if user_picture:
                # st.image(user_picture, width=50)
                st.markdown("👤")  # Default user icon emoji
            else:
                st.markdown("👤")  # Default user icon emoji
        with col2:
            st.write(f"Welcome, {user_info['name']}")

        # Logout and Reset buttons
        if st.button("Logout"):
            logout()
            st.rerun()
        
        if st.button("Reset Q&A Session"):
            init_session_state()

    # Messages in the conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Chat input that invokes the agent
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.empty():
                with st.spinner():
                    response = bedrock_agent_runtime.invoke_agent(
                        agent_id,
                        agent_alias_id,
                        st.session_state.session_id,
                        prompt
                    )
            output_text = response["output_text"]

            # An agent that uses Titan as the FM and has knowledge bases attached may return a JSON object with the
            # instruction and result fields
            st.session_state.titan_citation_style = False
            try:
                # When parsing the JSON, strict mode must be disabled to handle badly escaped newlines
                output_json = json.loads(output_text, strict=False)
                if "instruction" in output_json and "result" in output_json:
                    output_text = output_json["result"]
                    st.session_state.titan_citation_style = "%[X]%" in output_json["instruction"]
            except json.JSONDecodeError as e:
                pass

            # Add citations
            if len(response["citations"]) > 0:
                citation_nums = []

                # Citations in response from agents that use Titan as the FM may be out sequence
                # Thus we need to renumber them
                def replace_citation(match):
                    global citation_nums
                    orig_citation_num = match.group(1)
                    citation_nums.append(orig_citation_num)
                    return f"<sup>[{orig_citation_num}]</sup>"

                if st.session_state.titan_citation_style:
                    output_text = re.sub(r"%\[(\d+)\]%", replace_citation, output_text)

                i = 0
                citation_locs = {}
                for citation in response["citations"]:
                    for retrieved_ref in citation["retrievedReferences"]:
                        citation_num = i + 1
                        if st.session_state.titan_citation_style:
                            citation_num = citation_nums[i]
                        if citation_num not in citation_locs.keys():
                            citation_marker = f"[{citation_num}]"
                            match retrieved_ref['location']['type']:
                                case 'CONFLUENCE':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['confluenceLocation']['url']}"
                                case 'CUSTOM':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['customDocumentLocation']['id']}"
                                case 'KENDRA':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['kendraDocumentLocation']['uri']}"
                                case 'S3':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['s3Location']['uri']}"
                                case 'SALESFORCE':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['salesforceLocation']['url']}"
                                case 'SHAREPOINT':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['sharePointLocation']['url']}"
                                case 'SQL':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['sqlLocation']['query']}"
                                case 'WEB':
                                    citation_locs[citation_num] = f"{retrieved_ref['location']['webLocation']['url']}"
                                case _:
                                    logger.warning(f"Unknown location type: {retrieved_ref['location']['type']}")
                        i += 1
                citation_locs = dict(sorted(citation_locs.items(), key=lambda item: int(item[0])))
                st.session_state.citation_nums = citation_nums

                output_text += "\n"
                for citation_num, citation_loc in citation_locs.items():
                    output_text += f"\n<br>[{citation_num}] {citation_loc}"

            st.session_state.messages.append({"role": "assistant", "content": output_text})
            st.session_state.citations = response["citations"]
            st.session_state.trace = response["trace"]
            st.markdown(output_text, unsafe_allow_html=True)

def render_trace_section():
    """Render the trace section in the sidebar"""
    trace_types_map = {
        "Pre-Processing": ["preGuardrailTrace", "preProcessingTrace"],
        "Orchestration": ["orchestrationTrace"],
        "Post-Processing": ["postProcessingTrace", "postGuardrailTrace"]
    }

    trace_info_types_map = {
        "preProcessingTrace": ["modelInvocationInput", "modelInvocationOutput"],
        "orchestrationTrace": ["invocationInput", "modelInvocationInput", "modelInvocationOutput", "observation", "rationale"],
        "postProcessingTrace": ["modelInvocationInput", "modelInvocationOutput", "observation"]
    }

    with st.sidebar:
        st.title("Trace")

        # Show each trace type in separate sections
        step_num = 1
        for trace_type_header in trace_types_map:
            st.subheader(trace_type_header)

            # Organize traces by step similar to how it is shown in the Bedrock console
            has_trace = False
            for trace_type in trace_types_map[trace_type_header]:
                if trace_type in st.session_state.trace:
                    has_trace = True
                    trace_steps = {}

                    for trace in st.session_state.trace[trace_type]:
                        # Each trace type and step may have different information for the end-to-end flow
                        if trace_type in trace_info_types_map:
                            trace_info_types = trace_info_types_map[trace_type]
                            for trace_info_type in trace_info_types:
                                if trace_info_type in trace:
                                    trace_id = trace[trace_info_type]["traceId"]
                                    if trace_id not in trace_steps:
                                        trace_steps[trace_id] = [trace]
                                    else:
                                        trace_steps[trace_id].append(trace)
                                    break
                        else:
                            trace_id = trace["traceId"]
                            trace_steps[trace_id] = [
                                {
                                    trace_type: trace
                                }
                            ]

                    # Show trace steps in JSON similar to the Bedrock console
                    for trace_id in trace_steps.keys():
                        with st.expander(f"Trace Step {str(step_num)}", expanded=False):
                            for trace in trace_steps[trace_id]:
                                trace_str = json.dumps(trace, indent=2)
                                st.code(trace_str, language="json", line_numbers=True, wrap_lines=True)
                        step_num += 1
            if not has_trace:
                st.text("None")

        st.subheader("Citations")
        if len(st.session_state.citations) > 0:
            unique_citation_counts = {}
            i = 0
            for citation in st.session_state.citations:
                for retrieved_ref in citation["retrievedReferences"]:
                    citation_num = f"{i + 1}"
                    if st.session_state.titan_citation_style:
                        citation_num = st.session_state.citation_nums[i]
                    if citation_num not in unique_citation_counts.keys():
                        unique_citation_counts[citation_num] = 1
                    else:
                        unique_citation_counts[citation_num] += 1
                    with st.expander(f"Citation [{citation_num}] - Reference {unique_citation_counts[citation_num]}", expanded=False):
                        citation_str = json.dumps(
                            {
                                "generatedResponsePart": citation["generatedResponsePart"],
                                "retrievedReference": retrieved_ref
                            },
                            indent=2
                        )
                        st.code(citation_str, language="json", line_numbers=True, wrap_lines=True)
                    i += 1
        else:
            st.text("None")

def main():
    """Main application entry point"""
    st.set_page_config(page_title=ui_title, page_icon=ui_icon, layout="wide")
    
    # Initialize authentication
    init_auth_state()
    
    # Initialize session state
    init_session_state()
    
    # Handle user info from callback
    if st.session_state.get('user_info'):
        login(st.session_state['user_info'])
        del st.session_state['user_info']
    
    # Check authentication
    if not check_auth():
        render_login_page()
        return

    render_main_app(st.session_state.auth_state['user'])
    render_trace_section()

if __name__ == "__main__":
    main()
