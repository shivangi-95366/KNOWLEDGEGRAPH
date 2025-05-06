import spacy
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")

def create_knowledge_graph(text):
    doc = nlp(text)
    G = nx.DiGraph()
    
    # Add entities with sentiment
    for ent in doc.ents:
        sentiment = TextBlob(ent.text).sentiment.polarity
        G.add_node(ent.text, 
                  type='entity',
                  entity_type=ent.label_,
                  sentiment=sentiment,
                  color=get_color_for_sentiment(sentiment))
    
    # Add relationships
    for token in doc:
        if token.dep_ in ('nsubj', 'dobj'):
            # Add nodes if not present
            for node_text in [token.head.text, token.text]:
                if node_text not in G.nodes():
                    sentiment = TextBlob(node_text).sentiment.polarity
                    G.add_node(node_text,
                              type='word',
                              sentiment=sentiment,
                              color=get_color_for_sentiment(sentiment))
            
            # Add edge
            G.add_edge(token.head.text, token.text, label=token.dep_)
    
    return G

def visualize_graph(G):
    plt.figure(figsize=(12, 8))
    
    # Prepare node colors and sizes
    node_colors = [G.nodes[node]['color'] for node in G.nodes()]
    node_sizes = [1200 if G.nodes[node].get('type') == 'entity' else 800 
                 for node in G.nodes()]
    
    pos = nx.spring_layout(G, k=0.5)
    
    nx.draw(G, pos, 
           node_color=node_colors,
           node_size=node_sizes,
           font_size=10,
           arrowsize=20,
           edge_color='#777777')
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    plt.axis('off')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode()

def get_color_for_sentiment(sentiment):
    if sentiment > 0.1:
        return '#90EE90'  # Light green
    elif sentiment < -0.1:
        return '#FFA07A'  # Light salmon
    return '#A0CBE2'     # Light blue