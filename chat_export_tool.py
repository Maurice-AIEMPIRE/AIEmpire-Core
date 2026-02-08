#!/usr/bin/env python3
"""
Chat Export Tool - Maurice's AI Empire
Converts chat exports to clean TXT/Markdown/Word structures
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path


class ChatExporter:
    """Exports chat conversations to multiple formats"""
    
    def __init__(self, output_dir="exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def export_to_txt(self, messages, filename=None, title="Chat Export"):
        """Export messages to plain text format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_export_{timestamp}.txt"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("="*80 + "\n")
            f.write(f"{title}\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Messages
            for i, msg in enumerate(messages, 1):
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                
                f.write(f"[{i}] {role}")
                if timestamp:
                    f.write(f" - {timestamp}")
                f.write("\n")
                f.write("-" * 80 + "\n")
                f.write(content + "\n\n")
        
        return output_path
    
    def export_to_markdown(self, messages, filename=None, title="Chat Export"):
        """Export messages to Markdown format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_export_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {title}\n\n")
            f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Messages
            for i, msg in enumerate(messages, 1):
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                
                f.write(f"## [{i}] {role}")
                if timestamp:
                    f.write(f" - {timestamp}")
                f.write("\n\n")
                
                # Format content
                f.write(content + "\n\n")
                f.write("---\n\n")
        
        return output_path
    
    def export_to_docx_markdown(self, messages, filename=None, title="Chat Export"):
        """Export messages to Markdown format optimized for Word conversion"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_export_{timestamp}_word.md"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Title page
            f.write(f"# {title}\n\n")
            f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Messages:** {len(messages)}\n\n")
            f.write("\\newpage\n\n")  # Page break marker
            
            # Table of Contents
            f.write("## Table of Contents\n\n")
            for i, msg in enumerate(messages, 1):
                role = msg.get('role', 'unknown').capitalize()
                f.write(f"{i}. [{role}](#message-{i})\n")
            f.write("\n\\newpage\n\n")
            
            # Messages
            for i, msg in enumerate(messages, 1):
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                
                f.write(f"## Message {i}: {role} {{#message-{i}}}\n\n")
                if timestamp:
                    f.write(f"**Time:** {timestamp}\n\n")
                
                f.write(content + "\n\n")
                f.write("---\n\n")
        
        return output_path
    
    def parse_chatgpt_export(self, export_file):
        """Parse ChatGPT JSON export format"""
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = []
        
        # Handle different ChatGPT export formats
        if isinstance(data, list):
            # Format: Array of conversations
            for conversation in data:
                if 'mapping' in conversation:
                    # Extract messages from mapping structure
                    for node_id, node in conversation['mapping'].items():
                        if node.get('message'):
                            msg = node['message']
                            if msg.get('content') and msg['content'].get('parts'):
                                messages.append({
                                    'role': msg.get('author', {}).get('role', 'unknown'),
                                    'content': '\n'.join(msg['content']['parts']),
                                    'timestamp': datetime.fromtimestamp(
                                        msg.get('create_time', 0)
                                    ).strftime('%Y-%m-%d %H:%M:%S') if msg.get('create_time') else ''
                                })
        elif isinstance(data, dict):
            # Format: Single conversation
            if 'mapping' in data:
                for node_id, node in data['mapping'].items():
                    if node.get('message'):
                        msg = node['message']
                        if msg.get('content') and msg['content'].get('parts'):
                            messages.append({
                                'role': msg.get('author', {}).get('role', 'unknown'),
                                'content': '\n'.join(msg['content']['parts']),
                                'timestamp': datetime.fromtimestamp(
                                    msg.get('create_time', 0)
                                ).strftime('%Y-%m-%d %H:%M:%S') if msg.get('create_time') else ''
                            })
        
        return messages
    
    def parse_simple_format(self, export_file):
        """Parse simple text format (one message per section)"""
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        messages = []
        # Simple parser for text exports
        # Format: [ROLE] ... content ... [/ROLE]
        current_role = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('[') and ']' in line and not line.startswith('[/'):
                # New message start
                if current_role:
                    messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': ''
                    })
                current_role = line.split(']')[0][1:]
                current_content = []
            elif line.startswith('[/'):
                # Message end
                if current_role:
                    messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip(),
                        'timestamp': ''
                    })
                current_role = None
                current_content = []
            else:
                if current_role:
                    current_content.append(line)
        
        # Add last message if exists
        if current_role:
            messages.append({
                'role': current_role,
                'content': '\n'.join(current_content).strip(),
                'timestamp': ''
            })
        
        return messages


def main():
    parser = argparse.ArgumentParser(
        description='Export chat conversations to clean formats (TXT, Markdown, Word)'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input file (JSON from ChatGPT export or text file)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'md', 'word', 'all'],
        default='all',
        help='Export format (default: all)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='exports',
        help='Output directory (default: exports/)'
    )
    parser.add_argument(
        '-t', '--title',
        default='Chat Export',
        help='Title for the export'
    )
    parser.add_argument(
        '--example',
        action='store_true',
        help='Generate example export'
    )
    
    args = parser.parse_args()
    
    exporter = ChatExporter(output_dir=args.output_dir)
    
    # Generate example if requested
    if args.example:
        print("📝 Generating example chat export...")
        example_messages = [
            {
                'role': 'user',
                'content': 'Hallo! Ich möchte ein AI Empire System aufbauen.',
                'timestamp': '2026-02-08 10:00:00'
            },
            {
                'role': 'assistant',
                'content': 'Hallo Maurice! Das ist ein großartiges Ziel. Lass uns strukturiert vorgehen:\n\n1. **System-Architektur**: OpenClaw + Ollama + Claude\n2. **Automatisierung**: 9 Cron Jobs für Content & Revenue\n3. **Monetarisierung**: Gumroad Products + Fiverr Gigs\n\nWo möchtest du starten?',
                'timestamp': '2026-02-08 10:01:15'
            },
            {
                'role': 'user',
                'content': 'Ich brauche ein Chat Export Tool.',
                'timestamp': '2026-02-08 10:02:30'
            },
            {
                'role': 'assistant',
                'content': 'Perfekt! Ich erstelle dir ein Chat Export Tool mit:\n\n- TXT Format (einfach lesbar)\n- Markdown Format (strukturiert)\n- Word-kompatibles Format\n- ChatGPT JSON Parser\n\nDas Tool wird in chat_export_tool.py gespeichert.',
                'timestamp': '2026-02-08 10:03:00'
            }
        ]
        
        if args.format in ['txt', 'all']:
            path = exporter.export_to_txt(example_messages, title=args.title)
            print(f"✅ TXT export: {path}")
        
        if args.format in ['md', 'all']:
            path = exporter.export_to_markdown(example_messages, title=args.title)
            print(f"✅ Markdown export: {path}")
        
        if args.format in ['word', 'all']:
            path = exporter.export_to_docx_markdown(example_messages, title=args.title)
            print(f"✅ Word-ready export: {path}")
            print(f"   Convert to DOCX with: pandoc {path} -o {path.stem}.docx")
        
        return
    
    # Process input file
    if not args.input_file:
        parser.print_help()
        print("\n💡 Tip: Use --example to generate a sample export")
        return
    
    if not os.path.exists(args.input_file):
        print(f"❌ Error: File not found: {args.input_file}")
        return
    
    print(f"📂 Reading: {args.input_file}")
    
    # Try to parse as JSON first (ChatGPT export)
    try:
        messages = exporter.parse_chatgpt_export(args.input_file)
        print(f"✅ Parsed ChatGPT export: {len(messages)} messages")
    except (json.JSONDecodeError, KeyError):
        # Try simple text format
        messages = exporter.parse_simple_format(args.input_file)
        print(f"✅ Parsed text format: {len(messages)} messages")
    
    if not messages:
        print("⚠️  Warning: No messages found in export")
        return
    
    # Export to requested formats
    if args.format in ['txt', 'all']:
        path = exporter.export_to_txt(messages, title=args.title)
        print(f"✅ TXT export: {path}")
    
    if args.format in ['md', 'all']:
        path = exporter.export_to_markdown(messages, title=args.title)
        print(f"✅ Markdown export: {path}")
    
    if args.format in ['word', 'all']:
        path = exporter.export_to_docx_markdown(messages, title=args.title)
        print(f"✅ Word-ready export: {path}")
        print(f"   Convert to DOCX with: pandoc {path} -o {path.stem}.docx")
    
    print("\n🎉 Export complete!")


if __name__ == '__main__':
    main()
