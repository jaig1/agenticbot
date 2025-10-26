#!/usr/bin/env python3
"""
Test script to demonstrate the improved pricing response formatting
"""

def clean_pricing_response(content: str) -> str:
    """
    Clean and format pricing agent responses for better readability.
    Specifically formats tool calls to be on separate lines with clear descriptions.
    
    Args:
        content: Raw pricing response content
        
    Returns:
        Cleaned and formatted content with readable tool call information
    """
    if not content:
        return content
    
    # Check if this is a pricing response with tool calls
    if "Tool calls made:" not in content:
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
        else:
            # Fallback: try to detect tool patterns manually
            tool_indicators = ["search", "pricing", "sku", "cost", "tool", "retrieved", "calculated"]
            sentences = tool_section.replace("→", " → ").split(".")
            bullet_parts = []
            for sentence in sentences:
                sentence = sentence.strip()
                if any(indicator in sentence.lower() for indicator in tool_indicators):
                    bullet_parts.append(sentence)
        
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
            
            # Add numbering and icons based on content
            if "search" in clean_part.lower():
                icon = "🔍"
                label = "Service Search"
            elif "pricing" in clean_part.lower() and ("detail" in clean_part.lower() or "sku" in clean_part.lower()):
                icon = "💰"
                label = "Pricing Details"
            elif "retrieved" in clean_part.lower() or "options" in clean_part.lower():
                icon = "📋"
                label = "SKU Retrieval"
            elif "calculat" in clean_part.lower() or "cost" in clean_part.lower():
                icon = "🧮"
                label = "Cost Calculation"
            else:
                icon = "🔧"
                label = "Tool Call"
            
            # Format the tool call with clear structure
            formatted_tools.append(f"{icon} **{label}**: {clean_part}")
        
        # Reconstruct the response with better formatting
        if formatted_tools:
            tools_text = "\n\n".join(formatted_tools)  # Double line breaks for better spacing
            return f"{main_response}\n\n---\n\n**🔧 API Tool Execution Details:**\n\n{tools_text}"
        else:
            return main_response
            
    except Exception as e:
        # If parsing fails, return original content
        print(f"Error cleaning pricing response: {e}")
        return content


def test_formatting():
    """Test the formatting with the problematic response from the user"""
    
    # The unreadable response the user reported
    raw_response = """The cost for 3 million Gemini input tokens is $1.50. This is based on the "Gemini Pro Input Tokens" SKU, which is priced at $0.50 per 1 million tokens.
Tool calls made: • Search service tool: searched for 'Gemini API' → found service ID AEFD-7695-64FA from cache • Get pricing options tool: retrieved SKUs for service AEFD-7695-64FA with filter 'input token' → found 98 pricing items • Get pricing details tool: got pricing for SKU AC9B-C746-1501 → 0.5USDper1Mcounts•Calculatecosttool:calculatedcostfor3000000inputtokensat0.5USDper1Mcounts•Calculatecosttool:calculatedcostfor3000000inputtokensat0.5 → total $1.5"""
    
    print("🔴 BEFORE (Unreadable):")
    print("=" * 80)
    print(raw_response)
    print()
    
    print("🟢 AFTER (Cleaned & Formatted):")
    print("=" * 80)
    cleaned = clean_pricing_response(raw_response)
    print(cleaned)
    print()
    
    print("✅ Formatting improvements:")
    print("- Tool calls are on separate lines")
    print("- Each tool has a clear icon and label")
    print("- Better visual separation with section dividers")
    print("- Proper line spacing for readability")
    print("- Arrow symbols are standardized")


if __name__ == "__main__":
    test_formatting()
