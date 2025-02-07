# GitHub Releases Summary Tool

A professional tool designed to summarize recent changes in GitHub repositories by analyzing their releases. This application leverages Large Language Models (LLMs) to generate concise summaries, helping you stay updated with the latest repository changes effortlessly.

## 🚀 **How to Use?**

1. Links to [App](https://app-releases-summary.streamlit.app/)

2. **Choose LLM Response Language**  
   Select your preferred language for the summary output, including English, Chinese (Traditional/Simplified), Spanish, French, German, and more.

3. **Select LLM Model**  
   - **OpenAI**: Supports models like GPT-4o.  
   - **ZhipuAI** (Free): A cost-effective option for generating summaries.  
     - If you'd like to deploy ZhipuAI locally, refer to [chatgpt-line-bot](https://github.com/your-link-here) for API application guidance.

4. **Manage GitHub Repositories**  
   - Add or remove repositories to be summarized.  
   - Simply input the GitHub repository URL (e.g., `https://github.com/user/repo`) or repository name (`user/repo`).  
   - Repositories will be stored in the internal database for easy tracking.

5. **Set Tracking Duration**  
   - Define the number of days (`n`) to track recent releases.  
   - The tool will summarize all changes within this timeframe.

6. **Generate Summaries**  
   - Start summarizing with a single click.  
   - The tool fetches release data, analyzes key changes, and outputs concise summaries using the selected LLM.
