#!/bin/bash
# Install GraphIt packages for testing

echo "Installing GraphIt packages..."

# Install base package first (required by others)
cd graphit-base
pip install -e .
cd ..

# Install base package first (required by others)
cd graphit-cli
pip install -e .
cd ..

# Install vertexai package (depends on base)
cd graphit-vertexai  
pip install -e .
cd ..

# Install flow package (for additional components)
cd graphit-flow
pip install -e .
cd ..

echo "Package installation complete!"
echo "Verify installation:"
#python -c "import graphit.model.text_completion.vertexai.llm; print('VertexAI import successful')"
