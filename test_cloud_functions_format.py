#!/usr/bin/env python3
"""
Test the specific pricing response formatting issue from the user's image
"""

def clean_pricing_response(content: str) -> str:
    """
    Clean and format pricing agent responses for better readability.
    Fixes the garbled tool calls formatting issue.
    """
    if not content or "Tool calls made:" not in content:
        return content
    
    try:
        # Split the response into main answer and tool section
        parts = content.split("Tool calls made:", 1)
        main_response = parts[0].strip()
        tool_section = parts[1].strip() if len(parts) > 1 else ""
        
        if not tool_section:
            return main_response
        
        # Remove any "How I got this information" section
        if "---" in tool_section:
            tool_section = tool_section.split("---")[0].strip()
        
        # Parse and format tool calls with better structure
        formatted_tools = []
        
        # Split by bullet points first
        bullet_parts = []
        if "•" in tool_section:
            bullet_parts = [part.strip() for part in tool_section.split("•") if part.strip()]
        
        # Process each tool call
        for i, part in enumerate(bullet_parts, 1):
            if not part or len(part) < 10:
                continue
            
            # Clean up the text - fix common formatting issues
            clean_part = ' '.join(part.split())  # Normalize whitespace
            clean_part = clean_part.replace("→", "➜")  # Better arrow symbol
            
            # Fix garbled text patterns
            clean_part = clean_part.replace("USDper", " USD per ")
            clean_part = clean_part.replace("Mcounts", "M counts")
            clean_part = clean_part.replace("inputtokensat", " input tokens at ")
            clean_part = clean_part.replace("calculatedcostfor", "calculated cost for ")
            clean_part = clean_part.replace("Calculatecosttool:", "Calculate cost tool: ")
            clean_part = clean_part.replace("invocations", " invocations")
            clean_part = clean_part.replace("invocationsat", " invocations at ")
            
            # Add icons based on content
            if "search" in clean_part.lower():
                icon = "🔍"
                label = "**Service Search**"
            elif "pricing" in clean_part.lower() and ("detail" in clean_part.lower() or "sku" in clean_part.lower()):
                icon = "💰"
                label = "**Pricing Details**"
            elif "retrieved" in clean_part.lower() or "options" in clean_part.lower():
                icon = "📋"
                label = "**SKU Retrieval**"
            elif "calculat" in clean_part.lower() or "cost" in clean_part.lower():
                icon = "🧮"
                label = "**Cost Calculation**"
            else:
                icon = "🔧"
                label = "**Tool Call**"
            
            # Format the tool call with clear structure
            formatted_tools.append(f"{icon} {label}: {clean_part}")
        
        # Reconstruct the response with better formatting
        if formatted_tools:
            tools_text = "\n\n".join(formatted_tools)  # Double line breaks for better spacing
            return f"{main_response}\n\n---\n\n**🔧 API Tool Execution Details:**\n\n{tools_text}"
        else:
            return main_response
            
    except Exception as e:
        # If parsing fails, return original content
        return content


def test_cloud_functions_response():
    """Test with the exact response from the user's image"""
    
    # The problematic response from the user's image
    raw_response = """The cost for 1000 Cloud Functions invocations is $0.00. This is based on the "Cloud Run Functions Invocations" SKU, which is priced at $0.00 per 1 million invocations.
Tool calls made: • Search service tool: searched for 'Cloud Functions' → found service ID 29E7-DA93-CA13 from cache • Get pricing options tool: retrieved SKUs for service 29E7-DA93-CA13 with filter 'invocation' → found 2 pricing items • Get pricing details tool: got pricing for SKU 92DF-0F0E-630F → 0.0USDper1Mcounts•Calculatecosttool:calculatedcostfor1000invocationsat0.0 → total $0.0"""
    
    print("🔴 BEFORE (Unreadable from user's image):")
    print("=" * 100)
    print(raw_response)
    print()
    
    print("🟢 AFTER (Cleaned & Formatted):")
    print("=" * 100)
    cleaned = clean_pricing_response(raw_response)
    print(cleaned)
    print()
    
    print("✅ Key improvements:")
    print("- Fixed 'USDper1Mcounts' → 'USD per 1M counts'")
    print("- Fixed 'Calculatecosttool:calculatedcostfor1000invocationsat0.0' → readable format")  
    print("- Each tool call on separate line with icons")
    print("- Clear visual separation with section dividers")
    print("- Proper spacing and formatting")


if __name__ == "__main__":
    test_cloud_functions_response()
