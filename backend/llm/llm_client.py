from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
# from langchain_groq import ChatGroq
# from langchain.chat_models import init_chat_model


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    # llm = ChatGroq(
    # model_name="meta-llama/llama-4-scout-17b-16e-instruct",
    # temperature=0,
    # api_key=os.getenv("GROQ_API_KEY"),
    # )
    # return llm
#     model = init_chat_model(
#     model="xiaomi/mimo-v2-flash:free",
#         model_provider="openai",  # <-- REQUIRED

#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.getenv("OPENROUTER_API_KEY")
# )
#     return model


async def ask_llm(system_prompt: str, user_prompt: str) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    response = await llm.ainvoke(messages)
    
    # Extract content from response
    # LangChain response might have different structures
    content = None
    
    if hasattr(response, 'content'):
        content = response.content
        # Handle case where content is a list (some LangChain versions)
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and 'text' in content[0]:
                content = content[0]['text']
            else:
                content = str(content[0])
    elif isinstance(response, dict):
        # Try common keys
        content = response.get('content') or response.get('text') or str(response)
    else:
        content = str(response)
    
    if not isinstance(content, str):
        content = str(content)
    
    # Log raw response for debugging
    print(f"[LLM Response] Raw content (first 500 chars): {content[:500]}")
    
    # Clean JSON markdown formatting
    content = content.strip()
    
    # Remove markdown code blocks
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    # Remove any leading/trailing text that's not JSON
    # Find the first { and last }
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        content = content[first_brace:last_brace + 1]
    
    # Try to fix common JSON issues
    # Replace single quotes with double quotes (but be careful with strings)
    # This is a simple fix - for production, use a more robust approach
    try:
        # First try direct parse
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[LLM Response] JSON parse error: {e}")
        print(f"[LLM Response] Content causing error: {content[:500]}")
        
        # Try to extract JSON using regex
        import re
        # Match JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        if json_matches:
            # Try the largest match first
            for match in sorted(json_matches, key=len, reverse=True):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Last resort: try to fix common issues
        # Replace single quotes around keys and string values (simple case)
        fixed_content = re.sub(r"'(\w+)':", r'"\1":', content)
        fixed_content = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_content)
        
        try:
            return json.loads(fixed_content)
        except json.JSONDecodeError:
            # If all else fails, raise with helpful error
            raise ValueError(
                f"Failed to parse JSON from LLM response.\n"
                f"Error: {str(e)}\n"
                f"Content (first 1000 chars): {content[:1000]}\n"
                f"Please check the LLM response format."
            )    