# Agents for Amazon Bedrock Test UI

A generic Streamlit UI for testing generative AI agents built using Agents for Amazon Bedrock. For more information, refer to the blog post [Developing a Generic Streamlit UI to Test Amazon Bedrock Agents](https://blog.avangards.io/developing-a-generic-streamlit-ui-to-test-amazon-bedrock-agents).

# Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [Python 3](https://www.python.org/downloads/)
- [Google Cloud Console Account](https://console.cloud.google.com) (for authentication setup)

# Running Locally

1. Set up a Python virtual environment and install dependencies:

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. Set up Google OAuth 2.0 credentials:
   1. Go to [Google Cloud Console](https://console.cloud.google.com)
   2. Create a new project or select an existing one
   3. Enable the Google+ API
   4. Go to Credentials > Create Credentials > OAuth Client ID
   5. Configure the OAuth consent screen:
      - Select User Type (Internal for Google Workspace or External)
      - Fill in the required information
   6. Create OAuth Client ID:
      - Application type: Web application
      - Name: Your application name
      - Authorized redirect URIs: Add your application's callback URL
        - For local development: `http://localhost:8080/auth_callback`
        - For production: `https://your-domain.com/auth_callback`
   7. Note down the Client ID and Client Secret

3. Set the following environment variables either directly or using a `.env` file (use `.env.template` as a starting point):
   - `BEDROCK_AGENT_ID` - The ID of the agent.
   - `BEDROCK_AGENT_ALIAS_ID` - The ID of the agent alias. The default `TSTALIASID` will be used if it is not set.
   - The [AWS environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) that provides the credentials to your account. The principal must have the necessary permissions to invoke the Bedrock agent.
   - Google OAuth 2.0 credentials:
     * `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
     * `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret
     * `OAUTH_REDIRECT_URI` - The redirect URI (must match one configured in Google Cloud Console)
     * `ALLOWED_DOMAINS` - (Optional) Comma-separated list of allowed Google Workspace domains
4. (Optional) Set the following environment variables similarly to customize the UI:
   - `BEDROCK_AGENT_TEST_UI_TITLE` - The page title. The default `Agents for Amazon Bedrock Test UI` will used if it is not set.
   - `BEDROCK_AGENT_TEST_UI_ICON` - The favicon, such as `:bar_chart:`. The default Streamlit icon will be used if it is not set.
5. (Optional) Set the `LOG_LEVEL` environment variable for additional logging using a standard format. If more advanced configuration is needed, copy `logging.yaml.template` and `logging.yaml` and configure it as appropriate.
6. Run the application:

   For development with hot reload:
   ```bash
   # Enable hot reload and show full error messages
   streamlit run app.py --server.port=8080 --server.address=localhost --server.runOnSave=true --client.showErrorDetails=true
   ```

   For production:
   ```bash
   streamlit run app.py --server.port=8080 --server.address=localhost
   ```
