# SAR Generator - Complete Setup Guide

## Prerequisites
- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Windows/Mac/Linux

---

## STEP 1: Install Python Dependencies

### Create Project Directory
```bash
# Create project folder
mkdir sar-generator
cd sar-generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Install Python Packages
```bash
# Upgrade pip first
pip install --upgrade pip

# Core dependencies
pip install langchain==0.1.0
pip install langchain-community==0.0.13
pip install streamlit==1.29.0
pip install pandas==2.1.4
pip install numpy==1.26.2

# LLM and embeddings
pip install sentence-transformers==2.2.2
pip install chromadb==0.4.22

# Utilities
pip install python-dotenv==1.0.0
pip install pydantic==2.5.3
```

Create a `requirements.txt` file:
```bash
pip freeze > requirements.txt
```

---

## STEP 2: Install Ollama (Local LLM)

### For Windows:
1. Download from: https://ollama.ai/download/windows
2. Run the installer
3. Ollama will install and start automatically

### For Mac:
```bash
# Download and install
curl -fsSL https://ollama.ai/install.sh | sh
```

### For Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Verify Installation:
```bash
# Check Ollama is running
ollama --version

# Should output: ollama version is 0.x.x
```

---

## STEP 3: Download LLM Model

### Download Llama 3.2 (3B - Fast, Good for Demo)
```bash
ollama pull llama3.2

# This will download ~2GB, takes 5-10 minutes
```

### Test the Model:
```bash
ollama run llama3.2

# Type: Hello, how are you?
# Model should respond
# Type: /bye to exit
```

### Alternative: Mistral (7B - Better Quality, Slower)
```bash
ollama pull mistral
```

**Recommendation:** Start with `llama3.2` for speed during development.

---

## STEP 4: Verify Everything Works

### Test Script:
Create `test_setup.py`:
```python
import sys
print(f"Python version: {sys.version}")

try:
    import langchain
    print(f"✓ LangChain installed: {langchain.__version__}")
except:
    print("✗ LangChain not found")

try:
    import streamlit
    print(f"✓ Streamlit installed: {streamlit.__version__}")
except:
    print("✗ Streamlit not found")

try:
    import chromadb
    print(f"✓ ChromaDB installed: {chromadb.__version__}")
except:
    print("✗ ChromaDB not found")

try:
    from langchain_community.llms import Ollama
    llm = Ollama(model="llama3.2")
    response = llm.invoke("Say 'Setup complete!' and nothing else.")
    print(f"✓ Ollama working: {response.strip()}")
except Exception as e:
    print(f"✗ Ollama error: {e}")

print("\n✅ Setup verification complete!")
```

Run it:
```bash
python test_setup.py
```

Expected output:
```
Python version: 3.10.x
✓ LangChain installed: 0.1.0
✓ Streamlit installed: 1.29.0
✓ ChromaDB installed: 0.4.22
✓ Ollama working: Setup complete!

✅ Setup verification complete!
```

---

## TROUBLESHOOTING

### Issue: "ollama: command not found"
**Solution:** Restart your terminal after installing Ollama

### Issue: "Model not found"
**Solution:** 
```bash
ollama list  # Check available models
ollama pull llama3.2  # Re-download if needed
```

### Issue: "Port 11434 already in use"
**Solution:** Ollama is already running, you're good to go!

### Issue: ImportError for packages
**Solution:**
```bash
# Make sure virtual environment is activated
# Look for (venv) in your terminal prompt
pip install --upgrade -r requirements.txt
```

---

## NEXT STEPS

Once setup is complete:
1. Create project structure (folders)
2. Add sample data files
3. Build the SAR generator core
4. Create Streamlit UI

Setup time: ~30 minutes
Ready to code: YES! 🚀
