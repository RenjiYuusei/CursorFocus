## [All rights belong to RenjiYuusei please do not steal the source code or modify the source code without the author's consent. Please respect the author](https://github.com/RenjiYuusei/CursorFocus)

## CursorFocus

A lightweight tool that maintains a focused view of your project structure and environment. CursorFocus automatically tracks your project files, functions, and environment variables, updating every 60 seconds to keep you informed of changes.

Check out our [SHOWCASE.md](SHOWCASE.md) for detailed examples and real-world use cases!

## Discord

Join our Discord server to discuss features, ask questions: [Discord](https://discord.gg/N6FBdRZ8sw)

## Features

- 🤖 AI-powered rules generation
- 🔄 Real-time project structure tracking
- 📝 Automatic file and function documentation
- 🌳 Hierarchical directory visualization
- 📏 File length standards and alerts
- 🎯 Project-specific information detection
- 🎛️ Automatic .cursorrules generation and project adaptation

## Installation
```
irm https://raw.githubusercontent.com/RenjiYuusei/CursorFocus/refs/heads/main/install.ps1 | iex
```

## Requirements

- Python 3.10+
- Gemini API Key (required for AI-powered features)

## API Key Setup

Before running CursorFocus, you need to set up your Gemini API key:

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Set up the environment variable:

   For Windows:

   ```bash
   set GEMINI_API_KEY=your_api_key_here
   ```

   For Mac/Linux:

   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

   To make it permanent:

   - Windows: Add to system environment variables
   - Mac/Linux: Add to `~/.bashrc`, `~/.zshrc`, or equivalent shell config file

   Extra: Set manual environment variable
   Create a file called `.env` in the root of the project and add the following:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```


## Multi-Project Support

CursorFocus can monitor multiple projects simultaneously. There are two ways to set this up:


### Manual Setup

If you prefer to set up manually:

1. Install dependencies (Python 3.10+ required):

   ```bash
   cd CursorFocus
   pip install -r requirements.txt
   ```

2. Run the setup script:
   ```bash
   python setup.py --p path/to/your/project
   ```

3. Run the script:
   ```bash
   python focus.py
   ```

## Generated Files

CursorFocus automatically generates and maintains two key files:

1. **Focus.md**: Project documentation and analysis
   - Project overview and structure
   - File descriptions and metrics
   - Function documentation
2. **.cursorrules**: Project-specific Cursor settings
   - Support format: JSON, Markdown
   - Automatically generated based on project type
   - Customized for your project's structure
   - Updates as your project evolves

## Output

CursorFocus generates a `Focus.md` file in your project root with:

1. Project Overview

   - Project name and description
   - Key features and version
   - Project type detection

2. Project Structure

   - Directory hierarchy
   - File descriptions
   - Function listings with detailed descriptions
   - File type detection
   - File length alerts based on language standards

3. Code Analysis
   - Key function identification
   - Detailed function descriptions
   - File length standards compliance

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
