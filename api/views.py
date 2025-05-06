from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import spacy
import networkx as nx
import pdfplumber
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import io
import base64
import os
from django.conf import settings

nlp = spacy.load('en_core_web_sm')

def home(request):
    return render(request, 'home.html')

def extract_text(source, input_type, file=None):
    if input_type == 'content':
        return source.strip()
    elif input_type == 'pdf' and file:
        with pdfplumber.open(file) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif input_type == 'url':
        resp = requests.get(source.strip(), timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        return soup.get_text(separator="\n")
    return ""

def create_graph_image(text):
    doc = nlp(text)
    G = nx.DiGraph()
    
    # Improved graph creation with filtering
    for sent in doc.sents:
        for token in sent:
            if token.dep_ in ('nsubj', 'dobj') and not token.is_stop:
                G.add_edge(token.head.text, token.text, label=token.dep_)
    
    # Better visualization
    plt.figure(figsize=(12, 8))
    pos = nx.kamada_kawai_layout(G)
    
    nx.draw(G, pos, with_labels=True, 
            node_color='#1f78b4', 
            node_size=1000,
            font_size=9,
            edge_color='#666666',
            width=1.5,
            arrowsize=15)
    
    # Add edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode()

def generate_graph(request):
    graph_image = None
    error = None
    
    if request.method == 'POST':
        try:
            input_type = request.POST.get('input_type')
            source = request.POST.get('content') or request.POST.get('url') or ""
            
            if input_type == 'pdf':
                text = extract_text("", input_type, request.FILES.get('file'))
            else:
                text = extract_text(source, input_type)
            
            if text:
                graph_image = create_graph_image(text)
            else:
                error = "Please provide valid input"
                
        except Exception as e:
            error = f"Error processing input: {str(e)}"
    
    return render(request, 'knowledge_graph.html', {
        'graph_image': graph_image,
        'error': error
    })